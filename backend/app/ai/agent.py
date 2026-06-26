import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from sqlalchemy.orm import Session

from app.ai.conversation import (
    ConversationState,
    add_message,
    get_or_create_conversation,
    get_recent_history,
    load_state,
    save_state,
)
from app.ai.intent import classify_intent, filter_tools
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tools import make_context_tools
from app.models.product import Product
from app.models.user import User
from app.services.product_service import get_product_by_id as _get_product_by_id



def get_model(temperature: float = 0.1) -> ChatOllama:
    return ChatOllama(model="gemma4", temperature=temperature)


def _product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "price": p.price,
        "thumbnail": p.thumbnail,
        "rating": p.rating,
        "discount_percentage": p.discount_percentage,
        "brand": p.brand,
        "description": p.description,
        "review_count": p.review_count,
        "stock": p.stock,
    }


def _lookup_products(db: Session, ids: list[int]) -> list[dict]:
    result = []
    seen = set()
    for pid in ids:
        if pid in seen:
            continue
        seen.add(pid)
        try:
            p = _get_product_by_id(db, pid)
            result.append(_product_to_dict(p))
        except Exception:
            pass
    return result


def _make_state_block(state: ConversationState, db: Session) -> str:
    parts = []
    if state.last_query:
        parts.append(f"Last search: {state.last_query}")
        if state.last_filters:
            f = state.last_filters
            frags = []
            if f.get("category"): frags.append(f"category={f['category']}")
            if f.get("in_stock") is True: frags.append("in-stock only")
            elif f.get("in_stock") is False: frags.append("out-of-stock only")
            if f.get("min_price") is not None or f.get("max_price") is not None:
                frags.append(f"price={f.get('min_price','')}-{f.get('max_price','')}")
            if f.get("min_rating") is not None: frags.append(f"rating>={f['min_rating']}")
            if fragments := "; ".join(frags):
                parts.append(f"Filters: {fragments}")
        if state.last_sort and state.last_sort.get("sort_by"):
            parts.append(f"Sort: {state.last_sort['sort_by']} ({state.last_sort.get('sort_order', 'asc')})")
    if state.last_results:
        unique = list(dict.fromkeys(state.last_results))
        mappings = []
        for pid in unique:
            try:
                p = _get_product_by_id(db, pid)
                mappings.append(f"{p.title} (id={pid})")
            except Exception:
                mappings.append(f"id={pid}")
        parts.append("Products in context: " + "; ".join(mappings))
    return "\n".join(parts) if parts else "No previous search context."


def run_chat(
    db: Session,
    user: User,
    conversation_id: int | None,
    current_message: str,
) -> tuple[str, list[dict], int]:
    model = get_model()

    conversation = get_or_create_conversation(db, user.id, conversation_id)
    state = load_state(db, conversation.id)
    history = get_recent_history(db, conversation.id)
    tools = make_context_tools(db, user)

    intent = classify_intent(current_message)
    state.last_intent = intent
    allowed_tools = filter_tools(tools, intent)

    intent_context = f"\nUser intent: {intent}. Choose tools as needed to fulfill the request."
    messages = [SystemMessage(content=SYSTEM_PROMPT + intent_context)]

    state_block = _make_state_block(state, db)
    messages.append(SystemMessage(content=state_block))

    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            content = h["content"]
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=current_message))

    model_with_tools = model.bind_tools(allowed_tools)

    product_ids: list[int] = []
    cart_items_map: dict[int, dict] = {}
    response_text = ""
    last_tool_message = ""

    for iteration in range(6):
        result = model_with_tools.invoke(messages)

        if not result.tool_calls:
            response_text = (result.content or "").strip()
            if not response_text:
                if last_tool_message:
                    response_text = last_tool_message
                else:
                    response_text = "Sorry, I couldn't process that. Please try rephrasing."
            break

        messages.append(result)
        for tc in result.tool_calls:
            tool_result: dict = {}
            for t in allowed_tools:
                if t.name == tc["name"]:
                    try:
                        raw = t.invoke(tc["args"])
                        if isinstance(raw, dict):
                            tool_result = raw
                        else:
                            tool_result = {"message": str(raw)}
                    except Exception as e:
                        tool_result = {"error": str(e)}
                    break

            if tc["name"] == "get_cart_summary":
                for item in tool_result.get("items", []):
                    cart_items_map[item["product_id"]] = {
                        "cart_qty": item["quantity"],
                        "cart_subtotal": item["subtotal"],
                        "cart_unit_price": item["unit_price"],
                    }

            if tc["name"] == "search_products":
                args = tc["args"]
                state.last_query = args.get("query", state.last_query)
                filters = {}
                if args.get("category"): filters["category"] = args["category"]
                if args.get("in_stock") is not None: filters["in_stock"] = args["in_stock"]
                if args.get("min_price") is not None: filters["min_price"] = args["min_price"]
                if args.get("max_price") is not None: filters["max_price"] = args["max_price"]
                if args.get("min_rating") is not None: filters["min_rating"] = args["min_rating"]
                state.last_filters = filters or None
                sort = {}
                if args.get("sort_by"): sort["sort_by"] = args["sort_by"]
                if args.get("sort_order"): sort["sort_order"] = args["sort_order"]
                state.last_sort = sort or None
                if "product_ids" in tool_result:
                    state.last_results = tool_result["product_ids"]

            if tc["name"] in ("search_products", "get_cart_summary", "add_to_cart"):
                if "product_ids" in tool_result:
                    product_ids.extend(tool_result["product_ids"])
                if "product_id" in tool_result:
                    pid = tool_result["product_id"]
                    if pid and pid not in product_ids:
                        product_ids.append(pid)

            strip_keys = {"items"}
            if tc["name"] == "get_cart_summary":
                strip_keys |= {"product_ids"}
            msg_content = {k: v for k, v in tool_result.items() if k not in strip_keys}
            if "message" in msg_content:
                last_tool_message = msg_content["message"]
            messages.append(ToolMessage(
                content=json.dumps(msg_content, default=str),
                tool_call_id=tc["id"],
            ))

    if not response_text:
        response_text = "I'm having trouble processing your request. Please try again."

    add_message(db, conversation.id, "user", current_message)
    add_message(db, conversation.id, "assistant", response_text, product_ids=product_ids)
    save_state(db, conversation.id, state)

    products = _lookup_products(db, product_ids)
    if cart_items_map:
        for p in products:
            ci = cart_items_map.get(p["id"])
            if ci:
                p.update(ci)
    return response_text, products, conversation.id

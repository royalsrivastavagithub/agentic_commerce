import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from sqlalchemy.orm import Session

from app.ai.conversation import (
    ConversationState,
    add_message,
    get_or_create_conversation,
    get_recent_history,
)
from app.ai.intent import classify_intent, filter_tools
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tools import make_context_tools
from app.models.product import Product
from app.models.user import User
from app.services.product_service import get_product_by_id as _get_product_by_id


def _log_messages(messages: list, stage: str) -> None:
    print(f"\n=== MODEL MESSAGES ({stage}) ===")
    for i, m in enumerate(messages):
        role = type(m).__name__
        content = m.content if m.content else "(empty)"
        if hasattr(m, "tool_calls") and m.tool_calls:
            print(f"  [{i}] {role}: <{len(m.tool_calls)} tool_calls> content={content[:200]}")
            for tc in m.tool_calls:
                print(f"       -> {tc['name']}({json.dumps(tc['args'])})")
        else:
            print(f"  [{i}] {role}: {content[:300]}")
    print(f"=== END ({stage}) ===\n")


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


def run_chat(
    db: Session,
    user: User,
    conversation_id: int | None,
    current_message: str,
) -> tuple[str, list[dict], int]:
    model = get_model()
    state = ConversationState()

    conversation = get_or_create_conversation(db, user.id, conversation_id)
    history = get_recent_history(db, conversation.id)
    tools = make_context_tools(db, user)

    intent = classify_intent(current_message)
    state.last_intent = intent
    allowed_tools = filter_tools(tools, intent)

    intent_context = f"\nUser intent: {intent}. Choose tools as needed to fulfill the request."
    messages = [SystemMessage(content=SYSTEM_PROMPT + intent_context)]

    prev_ids: list[int] = []
    for h in history:
        if h["role"] == "assistant" and h.get("product_ids"):
            prev_ids.extend(h["product_ids"])

    if prev_ids:
        unique = list(dict.fromkeys(prev_ids))
        mappings = []
        for pid in unique:
            try:
                p = _get_product_by_id(db, pid)
                mappings.append(f"{p.title} (id={pid})")
            except Exception:
                mappings.append(f"id={pid}")
        context = "Products in context: " + "; ".join(mappings)
        messages.append(SystemMessage(content=context))
    else:
        messages.append(SystemMessage(content="No previous search context."))

    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            content = h["content"]
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=current_message))

    model_with_tools = model.bind_tools(allowed_tools)
    _log_messages(messages, f"initial (intent={intent})")

    product_ids: list[int] = []
    cart_items_map: dict[int, dict] = {}
    response_text = ""
    last_tool_message = ""

    for iteration in range(6):
        print(f"\n--- Iteration {iteration + 1} (intent={intent}) ---")
        result = model_with_tools.invoke(messages)
        print(f"Result content: {result.content!r}")
        if result.tool_calls:
            print(f"Tool calls: {[(tc['name'], tc['args']) for tc in result.tool_calls]}")

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

            print(f"Tool '{tc['name']}' result: {json.dumps(tool_result, default=str)[:300]}")

            if "product_ids" in tool_result:
                product_ids.extend(tool_result["product_ids"])
            if "product_id" in tool_result:
                pid = tool_result["product_id"]
                if pid and pid not in product_ids:
                    product_ids.append(pid)

            strip_keys = {"items"}
            if tc["name"] == "get_cart_summary":
                strip_keys |= {"product_ids", "total"}
            msg_content = {k: v for k, v in tool_result.items() if k not in strip_keys}
            if "message" in msg_content:
                last_tool_message = msg_content["message"]
            messages.append(ToolMessage(
                content=json.dumps(msg_content, default=str),
                tool_call_id=tc["id"],
            ))
        _log_messages(messages, f"after_iteration_{iteration + 1}")

    if not response_text:
        response_text = "I'm having trouble processing your request. Please try again."

    add_message(db, conversation.id, "user", current_message)
    add_message(db, conversation.id, "assistant", response_text, product_ids=product_ids)

    products = _lookup_products(db, product_ids)
    if cart_items_map:
        for p in products:
            ci = cart_items_map.get(p["id"])
            if ci:
                p.update(ci)
    return response_text, products, conversation.id

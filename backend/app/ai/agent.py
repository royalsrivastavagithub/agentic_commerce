import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from sqlalchemy.orm import Session

from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tools import make_tools
from app.core.exceptions import NotFoundError
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


def _deduplicate(products: list[Product]) -> list[Product]:
    seen: set[int] = set()
    result: list[Product] = []
    for p in products:
        if p.id not in seen:
            seen.add(p.id)
            result.append(p)
    return result


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


def run_chat(db: Session, user: User, history: list[dict], current_message: str) -> tuple[str, list[dict]]:
    model = get_model()
    found_products: list[Product] = []
    tools = make_tools(db, user, found_products)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=current_message))

    model_with_tools = model.bind_tools(tools)
    _log_messages(messages, "initial")

    for iteration in range(6):
        print(f"\n--- Iteration {iteration + 1} ---")
        result = model_with_tools.invoke(messages)
        print(f"Result content: {result.content!r}")
        if result.tool_calls:
            print(f"Tool calls: {[(tc['name'], tc['args']) for tc in result.tool_calls]}")

        if not result.tool_calls:
            response_text = result.content or ""

            if not response_text:
                return "Sorry, I couldn't process that. Please try rephrasing.", []

            mentioned_ids = set(int(m) for m in re.findall(r'\(ID:\s*(\d+)\)', response_text))
            existing_ids = {p.id for p in found_products}
            for pid in mentioned_ids - existing_ids:
                try:
                    p = _get_product_by_id(db, pid)
                    found_products.append(p)
                except NotFoundError:
                    pass

            captured = [p for p in found_products if p.id in mentioned_ids]

            clean_text = re.sub(r'\s*\(ID:\s*\d+\)', '', response_text)
            clean_text = clean_text.replace('**', '')
            return clean_text, [_product_to_dict(p) for p in _deduplicate(captured)]

        messages.append(result)
        for tc in result.tool_calls:
            tool_result = ""
            for t in tools:
                if t.name == tc["name"]:
                    tool_result = t.invoke(tc["args"]) or ""
                    break
            print(f"Tool '{tc['name']}' result ({len(tool_result)} chars): {tool_result[:200]}")
            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))
        _log_messages(messages, f"after_iteration_{iteration + 1}")

    return "I'm having trouble processing your request. Please try again.", [_product_to_dict(p) for p in _deduplicate(found_products)]

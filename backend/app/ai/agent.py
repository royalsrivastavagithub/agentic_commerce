from langchain_ollama import ChatOllama
from sqlalchemy.orm import Session

from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tools import make_tools
from app.models.user import User


def get_model(temperature: float = 0.1) -> ChatOllama:
    return ChatOllama(model="gemma4", temperature=temperature)


def run_chat(db: Session, user: User, history_text: str, current_message: str) -> str:
    model = get_model()
    tools = make_tools(db, user)

    context = SYSTEM_PROMPT
    if history_text:
        context += f"\n\n{history_text}"
    context += f"\n\nUser: {current_message}"

    model_with_tools = model.bind_tools(tools)
    max_turns = 6

    for turn in range(max_turns):
        result = model_with_tools.invoke(context)

        if not result.tool_calls:
            return result.content or ""

        for tc in result.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_result = None
            for t in tools:
                if t.name == tool_name:
                    tool_result = t.invoke(tool_args)
                    break
            context += f"\n\n[Tool {tool_name}({tool_args}) returned: {tool_result}]"

    return "I'm having trouble processing your request. Please try again."

ALLOWED_TOOLS = {"status"}


def dispatch(message):
    tool_name = message.get("name")
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError("blocked")
    return {"ok": True}

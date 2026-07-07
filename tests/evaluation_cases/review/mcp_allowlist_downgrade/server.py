ALLOWED_TOOLS = {"status"}

def validate(message):
    if not isinstance(message, dict) or "name" not in message:
        raise ValueError("invalid schema")
    return message

def dispatch(message):
    message = validate(message)
    tool_name = message["name"]
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError("blocked")
    return {"ok": True}

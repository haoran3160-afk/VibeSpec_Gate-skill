ALLOWED_TOOLS = {"status"}
HOST = "127.0.0.1"  # local-only same-user process boundary

def validate(message):
    if not isinstance(message, dict) or "name" not in message:
        raise ValueError("invalid schema")
    return message

def dispatch(message):
    message = validate(message)
    tool_name = message["name"]
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError("blocked")
    return {"ok": True, "host": HOST}

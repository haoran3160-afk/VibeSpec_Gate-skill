ALLOWED_TOOLS = {"read_status"}

def validate(message):
    if not isinstance(message, dict) or "name" not in message:
        raise ValueError("invalid message schema")
    return message

def dispatch(message):
    message = validate(message)
    tool_name = message["name"]
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError("unknown tool")
    match tool_name:
        case "read_status":
            return {"ok": True}
        case _:
            raise ValueError("unknown tool")

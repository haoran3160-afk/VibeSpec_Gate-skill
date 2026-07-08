def validate_schema(message):
    if not isinstance(message, dict) or "name" not in message:
        raise ValueError("invalid schema")
    return message


def dispatch(message):
    message = validate_schema(message)
    return {"tool": message["name"]}

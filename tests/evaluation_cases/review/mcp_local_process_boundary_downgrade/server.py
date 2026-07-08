HOST = "127.0.0.1"
ALLOWED_TOOLS = {"status"}


def validate_schema(message):
    if not isinstance(message, dict) or message.get("name") not in ALLOWED_TOOLS:
        raise ValueError("blocked")
    return message


def status_endpoint():
    message = validate_schema({"name": "status"})
    return {"scope": "local-only same-user process owner", "host": HOST, "tool": message["name"]}

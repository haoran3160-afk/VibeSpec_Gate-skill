TOOLS = {}


def dispatch(message):
    tool_name = message["name"]
    return TOOLS[tool_name](message)

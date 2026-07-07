def dispatch(message):
    tool_name = message["name"]
    return call_tool(tool_name, message["arguments"])

def call_tool(name, arguments):
    return {"name": name, "arguments": arguments}

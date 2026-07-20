TOOL_SCHEMA = {
    "name": "read_project_document",
    "description": "Read one project document by its logical identifier.",
    "inputSchema": {
        "type": "object",
        "properties": {"document_id": {"type": "string"}},
        "required": ["document_id"],
    },
}


def register_tools(server, document_service) -> None:
    server.register_tool(TOOL_SCHEMA, document_service.read_document)

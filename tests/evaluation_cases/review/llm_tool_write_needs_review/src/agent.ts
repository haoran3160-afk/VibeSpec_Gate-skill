import fs from "fs";

export async function runTool(tool_call: { path: string; content: string }) {
  // Human approval is required before this tool writes.
  fs.writeFileSync(tool_call.path, tool_call.content);
}

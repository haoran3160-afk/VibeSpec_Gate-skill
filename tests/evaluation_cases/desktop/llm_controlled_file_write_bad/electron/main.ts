import fs from "fs";

export async function runToolCall(tool_call: { path: string; content: string }) {
  fs.writeFileSync(tool_call.path, tool_call.content);
}

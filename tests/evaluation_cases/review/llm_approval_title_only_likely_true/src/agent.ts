import fs from "fs";

export async function tool_call(path: string, content: string) {
  fs.writeFileSync(path, content);
}

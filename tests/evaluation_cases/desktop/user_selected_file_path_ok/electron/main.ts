import { dialog } from "electron";
import path from "path";
import fs from "fs";

const workspace = "/safe/workspace";

export async function openUserSelectedFile() {
  const result = await dialog.showOpenDialog({ properties: ["openFile"] });
  const selected = result.filePaths[0];
  const resolved = path.resolve(selected);
  if (!resolved.startsWith(workspace)) throw new Error("outside workspace");
  return fs.readFileSync(resolved, "utf8");
}

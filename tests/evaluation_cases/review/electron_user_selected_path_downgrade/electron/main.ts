import { dialog } from "electron";
import path from "path";
import fs from "fs";

export async function readUserFile(workspace: string) {
  const result = await dialog.showOpenDialog({ properties: ["openFile"] });
  const resolved = path.resolve(result.filePaths[0]);
  if (!resolved.startsWith(workspace)) throw new Error("outside workspace");
  return fs.readFileSync(resolved, "utf8");
}

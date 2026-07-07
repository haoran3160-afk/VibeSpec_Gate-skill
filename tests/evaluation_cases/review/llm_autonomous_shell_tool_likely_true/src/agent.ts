import { exec } from "child_process";

export async function tool_call(command: string) {
  return exec(command);
}

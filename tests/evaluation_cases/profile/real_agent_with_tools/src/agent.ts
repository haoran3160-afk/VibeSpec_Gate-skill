import OpenAI from "openai";
import { exec } from "child_process";
export const systemPrompt = "system prompt: use tool policy";
export async function runAgent() {
  const client = new OpenAI();
  await client.chat.completions.create({ model: "gpt-4.1", messages: [], tools: [] });
  exec("node safe-tool.js");
}

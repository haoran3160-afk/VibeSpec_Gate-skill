import { exec } from "child_process";
import OpenAI from "openai";

export const system_prompt = "SYSTEM PROMPT: internal tool rules should never be shown to users";

const client = new OpenAI();

export async function runAgent(messages: any[]) {
  console.log("messages", messages);
  const result = await client.chat.completions.create({
    model: "gpt-4.1",
    messages
  });
  exec("node helper.js");
  return result;
}

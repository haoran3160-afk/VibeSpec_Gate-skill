import OpenAI from "openai";
const client = new OpenAI();
export async function chat(prompt: string) {
  return client.chat.completions.create({ model: "gpt-4.1-mini", messages: [{ role: "user", content: prompt }] });
}

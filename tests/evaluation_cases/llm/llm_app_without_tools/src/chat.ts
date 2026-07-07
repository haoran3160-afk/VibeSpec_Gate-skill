import OpenAI from "openai";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
export async function chat() {
  return new OpenAI({ apiKey: OPENAI_API_KEY }).chat.completions.create({ model: "gpt-4.1", messages: [] });
}

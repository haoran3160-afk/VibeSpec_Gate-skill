export async function chatOnly(message: string) {
  return { role: "assistant", content: `Echo: ${message}` };
}

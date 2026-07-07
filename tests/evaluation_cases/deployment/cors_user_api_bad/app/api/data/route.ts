export async function GET() {
  return new Response("{}", { headers: { "Access-Control-Allow-Origin": "*" } });
}

import { supabase } from "../../../lib/supabase";

export async function POST(req: Request) {
  const body = await req.json();
  return Response.json(await supabase.from("orders").insert(body));
}

export async function GET(req: Request) {
  const id = new URL(req.url).searchParams.get("id");
  return Response.json(await supabase.from("orders").select("*").eq("id", id));
}

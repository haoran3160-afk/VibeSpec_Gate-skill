export async function POST(req: Request) {
  const user = await requireAuth(req);
  if (!user) return new Response("Unauthorized", { status: 401 });
  return Response.json({ ok: true, userId: user.id });
}

async function requireAuth(_req: Request) {
  return { id: "demo-user" };
}

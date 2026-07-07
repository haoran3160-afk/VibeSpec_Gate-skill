export async function POST(request: Request) {
  const body = await request.json();
  await db.items.insert(body);
  return Response.json({ ok: true });
}

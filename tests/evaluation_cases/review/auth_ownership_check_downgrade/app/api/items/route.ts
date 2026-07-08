export async function GET(request: Request) {
  const user_id = request.headers.get("x-user-id");
  return db.items.findMany({ where: { user_id } });
}

export async function GET() {
  const orders = await database.orders.findMany();
  return Response.json(orders);
}

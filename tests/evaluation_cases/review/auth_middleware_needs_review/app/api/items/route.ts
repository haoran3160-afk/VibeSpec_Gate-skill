// Protected by middleware.ts before this route is reached.
export async function POST(request: Request) {
  const session = await getServerSession();
  return Response.json({ user: session?.user });
}

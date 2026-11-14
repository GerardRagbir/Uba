// Used by Docker's healthcheck to see that the frontend server is up.
export async function GET() {
  return Response.json({ status: "ok" });
}

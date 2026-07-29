export async function GET() {
  return Response.json({ ok: true, service: "GeoBancas RD", version: "1.0.0" });
}

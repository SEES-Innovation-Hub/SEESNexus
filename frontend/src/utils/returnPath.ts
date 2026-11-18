// ProtectedRoute sends visitors to /login with the page they wanted in the
// navigation state ({ from: "/projects/abc" }), so login can take them back.
// Only same-site paths are accepted: "//evil.com" would leave the site.
export function readReturnPath(state: unknown): string | null {
  const from = (state as { from?: unknown } | null)?.from;
  return typeof from === "string" && from.startsWith("/") && !from.startsWith("//") ? from : null;
}

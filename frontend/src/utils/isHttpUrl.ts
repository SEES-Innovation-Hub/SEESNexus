// Project links are user-supplied and shown on public pages: only http(s) is
// safe to use as an href (a "javascript:" URL would run script on click).
export function isHttpUrl(value: string | null): value is string {
  return value !== null && /^https?:\/\/\S+$/i.test(value);
}

// SQLite (local development) drops the time zone, so the API can answer
// "2026-11-10T09:00:00" for what was sent as 09:00 UTC, and new Date() would
// read that as local time: an hour off in Lagos. Postgres includes the zone.
// Both are UTC underneath, so a timestamp without a zone is read as UTC.
export function parseApiDate(value: string): Date {
  return new Date(/(Z|[+-]\d{2}:?\d{2})$/i.test(value) ? value : `${value}Z`);
}

# API deltas against Technical Documentation v2

§13 of the tech doc requires the document to be updated in the same PR as any schema or contract
change. The document itself is a PDF that cannot be edited from the repo, so each change is recorded
here for whoever holds the source file.

Each entry states the section affected, what the document says now, and what the running system does.

---

## §3 Tech Stack — Brevo SDK name

**Document:** "Brevo (sib-api-v3-sdk) — Transactional email/OTP".

**Implementation:** `brevo-python==5.1.0`.

Brevo replaced `sib-api-v3-sdk` with `brevo-python`. Two details matter to anyone reading the code:
the 5.x package imports as **`brevo`**, not `brevo_python`, and it ships a native async client
(`AsyncBrevo`), so the send is awaited directly rather than being pushed through a threadpool.

No route or schema is affected. Suggested replacement text for the table cell:
`Brevo (brevo-python; imports as brevo)`.

---

## §5.2 Notify — `/notify/send-code` response and failure modes

**Document:** "POST /send-code — Send OTP to email". No response body or error cases given.

**Implementation:**

- On success, `data` is `{"email": "<address>"}`.
- `data.debug_code` is included **only** when `OTP_DEBUG_RETURN_CODE` is true *and* `BREVO_API_KEY`
  is empty. Previously the flag alone controlled it, which meant a configured deployment handed the
  caller the secret it was about to test them on — anyone could have verified an address they did not
  own. The field now cannot appear in any environment that can send email.
- `502` when Brevo is configured and the send fails, with the standard error envelope and the message
  "Could not send the verification code. Please try again." The verification-code row is committed
  before the send is attempted, so a retry is safe.
- `message` distinguishes the two success paths: "Verification code sent" when email went out, and
  "Verification code generated, but email is not configured" otherwise, so a misconfigured deployment
  is loud rather than silently useless.

**Frontend impact:** `frontend/src/api/auth.ts` already types `debug_code` as optional, so no change
is required there. Any registration flow that depended on reading `debug_code` will stop working
against a deployment with a Brevo key — which is the intended behaviour.

---

## §4.2 Event / §5.5 Events — `virtual_link` visibility

**Document:** §4.2 lists `virtual_link` as "string, nullable" with no visibility rule. §5.5 gives
`GET /` and `GET /{id}` an Auth of "none".

**Implementation:** both routes remain public, exactly as §5.5 requires. `virtual_link` is returned as
`null` unless the caller is an `ADMIN` or holds a `CONFIRMED` registration for that event.

The document is silent on who may see the link, so withholding it contradicts nothing — but the
silence is worth closing explicitly, because the previous behaviour published a joinable meeting URL
to every anonymous visitor the moment an admin created the event. A **waitlisted** student is
deliberately excluded: they hold no place, which is the distinction waitlisting exists to draw.

Suggested addition to the §4.2 Event row: `virtual_link — string, nullable; returned only to an admin
or a confirmed registrant`.

---

## §5.5 Events — two new response fields

**Document:** no response schema is given for the event routes beyond the §4.2 column list.

**Implementation:** `EventResponse` gains two derived fields, on both the list and the detail route:

| Field | Type | Meaning |
|---|---|---|
| `confirmed_count` | int | Registrations with status `CONFIRMED`. Waitlisted and cancelled rows are not counted. |
| `spots_left` | int \| null | `max_participants - confirmed_count`, floored at 0. `null` when `max_participants` is `null`, matching §4.2's "nullable = unlimited". |

Both are additive, so no existing client breaks.

---

## §5.5 Events — new `upcoming` query parameter

**Document:** `GET /` is described only as "List events".

**Implementation:** `upcoming=true` restricts the list to events whose `start_date` has not passed.
Default is `false`, so the unfiltered behaviour is unchanged. The existing ordering
(`start_date` ascending) already suits the filter, so no sort parameter was added.

---

## §5.7 Admin — `total_events` excludes deleted events

**Document:** `GET /dashboard` — "Aggregate stats".

**Implementation:** `total_events` now counts only events with `deleted_at IS NULL`. Events are
soft-deleted, so the previous bare row count included events that no route will serve and that no
admin can see. `total_articles` has the same problem and will be fixed when Articles gains its
`deleted_at` column.

---

## §5.5 Events — `PUT /{id}` rejects an under-sized `max_participants`

**Document:** `PUT /{id}` — "Update event". No validation rules given.

**Implementation:** `400` when `max_participants` is set below the current `CONFIRMED` count, with the
count in the message. Lowering it would leave the event oversubscribed with no rule for whose place
was forfeited. This mirrors the existing guard in `adjust_total_quantity`
(`app/services/loans.py`), which refuses to drop a hardware quantity below the units on loan.

**Related fix, not a contract change.** The check is performed against the request payload *before*
any value is assigned to the event. Assigning first and validating afterwards is unsafe here: any
query issued after the assignment triggers a SQLAlchemy autoflush that writes the pending value, so a
rejected update could still reach the database. The pre-existing date validation
(`_validate_event_dates`) had the same shape and now rolls back explicitly before raising;
`test_rejected_date_update_does_not_persist` covers it and was confirmed to fail without the rollback.

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

## §4.2 Event / §5.5 Events — login required to read events; `virtual_link` visibility

**Document:** §4.2 lists `virtual_link` as "string, nullable" with no visibility rule. §5.5 gives
`GET /` and `GET /{id}` an Auth of "none".

**Implementation:** both routes now **require a login** (`401` without a valid access token), like
`/projects` and `/hardware`. On top of that, `virtual_link` is returned as `null` unless the caller is
an `ADMIN` or holds a `CONFIRMED` registration for that event. Waitlisted and cancelled students do
not get it: they hold no place.

Suggested change to §5.5: Auth for `GET /` and `GET /{id}` becomes "JWT (any role)". Suggested
addition to the §4.2 Event row: `virtual_link — string, nullable; returned only to an admin or a
confirmed registrant`.

**Frontend impact:** any public page (e.g. the landing page) that wants to show events must now
either be behind login or show static content.

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


---

## §5.5 Events — `GET /registrations/my`

**New route.** JWT, any role. Returns every registration the caller holds, in any status
(`CONFIRMED`, `WAITLISTED`, `CANCELLED`), with no filter on deadline or date, newest event first.

Each row is a registration plus:

| Field | Type | Meaning |
|---|---|---|
| `event` | Event | The full event, with the same `virtual_link` rule as elsewhere. |
| `waitlist_position` | int \| null | 1 = next in line. Null unless `WAITLISTED`. |
| `event_deleted` | bool | The organisers deleted the event after the student registered. |

---

## §5.5 Events — `DELETE /{id}/register` (cancel), and waitlist promotion

**New route.** JWT, any role. Cancels the caller's own registration (status becomes `CANCELLED`; the
row is kept). If the caller held a `CONFIRMED` place, the earliest `WAITLISTED` student
(by `registered_at`) is promoted to `CONFIRMED` in the same transaction.

- Allowed until the event's `start_date`, including after the registration deadline. `400` after.
- `404` if the caller has no live registration for the event.
- Registering again after cancelling re-uses the row and puts the student at the **back** of the
  queue (`registered_at` is reset).

**Also:** `PUT /{id}` now promotes waitlisted students when `max_participants` is raised or cleared to
`null` (unlimited), instead of leaving free places empty until someone cancels.

**Related fix:** `registered_at` is now set by the application on registration rather than by the
database default. SQLite's `CURRENT_TIMESTAMP` has one-second resolution, so students registering in
the same second tied and their waitlist order was arbitrary.

---

## §5.5 Events — restoring deleted events

**New:**

- `GET /?deleted=true` — admin only (`403` otherwise). Lists soft-deleted events instead of live ones.
- `GET /{id}` — an admin can open a deleted event; everyone else still gets `404`.
- `POST /{id}/restore` — admin only. Clears `deleted_at`. Registrations were never touched by the
  delete, so confirmed students keep their places. `400` if the event is not deleted.
- `EventResponse` gains `deleted_at` (always `null` for non-admins).

---

## §5.4 Hardware — `PUT /loans/{id}/cancel`, and a new `CANCELLED` loan status

**New route.** JWT, any role, but only the borrower: `403` for anyone else, admins included (admins
reject instead). Only a `PENDING` request can be withdrawn (`400` otherwise). The loan becomes
`CANCELLED`; `available_quantity` does not change, because units only move on approval.

`LoanStatus` gains `CANCELLED`, distinct from `REJECTED` so history shows who closed the request.
Migration `b7e2c5a91d04` adds the enum value.

---

## §5.6 Articles — implemented

**Document:** lists the Articles routes; the repo only had a stand-in table.

**Implementation:** `/api/v1/articles`, migration `b7e2c5a91d04`.

| Route | Who | Notes |
|---|---|---|
| `GET /` | JWT, any role | Paginated. Members see `PUBLISHED` only; admins see all. `mine=true` lists the caller's own, drafts included. Filters: `status`, `search` (title). Rows omit `content`. |
| `GET /{id_or_slug}` | JWT, any role | A draft is `404` to anyone but its author and admins. |
| `POST /` | `CONTRIBUTOR`, `ADMIN` | Slug generated from the title (`-2`, `-3` on clashes) unless given. Defaults to `DRAFT`. |
| `PUT /{id_or_slug}` | Author or `ADMIN` | The slug changes only if sent, so shared links survive a title edit. |
| `DELETE /{id_or_slug}` | Author or `ADMIN` | Soft delete (`deleted_at`). |

Fields: `id, title, slug, summary, content (Markdown), cover_image_url, status (DRAFT|PUBLISHED),
author_id, author {id, full_name, profile_image_url}, created_at, updated_at, published_at`.
`published_at` is set the first time an article is published and kept after that.

The admin dashboard's `total_articles` now excludes deleted articles.

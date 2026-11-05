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

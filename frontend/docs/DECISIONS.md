# SEES Nexus frontend — decision log

Covers the frontend work on **Auth UI, Profile and Landing** (plus the performance and image-generator work around them). The plan was set on 13–14 September 2026 and the work ran to 21 September; this log is kept up to date as decisions are made or changed.

**How to read this.** Each entry says what we decided, **why**, what it **cost or gave up**, where the code lives, and how we **checked** it. Entries that changed direction say so, because the reasons for a change matter as much as the change. For how the code is organised, see [CODE_GUIDE.md](./CODE_GUIDE.md).

## Contents

T. [Timeline: the work and every change of direction](#timeline-the-work-and-every-change-of-direction)
0. [Ground rules and scope](#0-ground-rules-and-scope)
1. [API layer and session](#1-api-layer-and-session)
2. [Auth UI](#2-auth-ui)
3. [Profile](#3-profile)
4. [Landing page](#4-landing-page)
5. [Look and feel](#5-look-and-feel)
6. [Performance and mobile](#6-performance-and-mobile)
7. [AI image generator](#7-ai-image-generator)
8. [How we verified things](#8-how-we-verified-things)
9. [Open items and deferred work](#9-open-items-and-deferred-work)

---

## Timeline: the work and every change of direction

Read this first for the story; the numbered sections below give the detail. The **Changed?** column is the important one: it records where we first did or thought one thing and then changed our mind, and why.

*Dates: 13-14 Sep are from the project notes, and the work between then and 20 Sep is reconstructed from the status summary at the start of the 20 Sep session and from the code. The exact days weren't recorded, so treat those rows as "before 20 Sep".*

### Before 20 September

| Step | What we did | Changed? |
|---|---|---|
| Scoping (13-14 Sep) | Read the Master Task Documentation and picked our slice: Auth UI, Profile, Landing. Turned v1's failure modes into acceptance criteria (no mock data, every backend route reachable, image uploads wired, Profile uses `/auth/me`, login redirects by role). All four pages were one-line stubs. | - |
| Auth build | Shared types, API client with silent token refresh, auth context and provider, `TextField`, `ProtectedRoute`, Login / Register / OTP screens, routes wired. The auth context was split into two files to satisfy a fast-refresh lint rule; `TextField` was extracted because several pages used it. | **Yes:** the first version sent every user to `/profile` after login. Re-reading Master Doc §3.1 ("redirects by role") showed we'd missed that, so `redirectPathForRole` was added. |
| Theme | v1's palette, gradients, shadows and fonts ported into Tailwind v4's CSS `@theme`. | - |
| Landing plan | Agreed to build the hero and layout for real, and build the project rail against the not-yet-built Projects contract, showing an empty state until the backend existed. | **Yes, on 20 Sep:** replaced by the real contract once the Projects backend merged. |
| Backend assumption | We believed the backend wasn't in the repo, so nothing could be tested end to end. | **Yes, 20 Sep:** wrong, it was committed. We then ran it and tested against it. |

### 20 September

| Step | What we did | Changed? |
|---|---|---|
| Re-verify Auth | Ran the real backend and the real API client together. Type-check and build were clean, but reading and running found **three bugs and a lint warning**. | **Yes:** the earlier summary said lint was "all clean"; it wasn't (one warning). |
| Fix: admin blank page | Admin login redirected to `/admin`, which has no page. Added a "Page not found" route. | Kept the spec'd redirect; only removed the blank screen. |
| Fix: burned OTP | A failed register left the user stuck on the OTP screen with a used-up code. | **Yes:** was "stay on the OTP screen with a generic error"; now "back to details with the backend's real message, inputs kept" (§2.2). |
| Fix: stale session | A hard redirect on failed refresh bounced public pages. | **Yes:** the docs say redirect to login; we now clear the session and let `ProtectedRoute` redirect (§1.3). |
| Fix: messages | Login said "Invalid email or password" for everything. | **Yes:** now shows the backend's own message. |
| Fix: context | Replaced the unused `refreshUser` with `updateProfile` (the `PUT` already returns the user). | **Yes** |
| Profile | Built view, edit (only changed fields), picture upload, log out. `/upload/image` didn't exist, so we chose to **build against an assumed contract** rather than ship a URL text box or skip the upload. | Option A of three (A: assumed contract, B: leave out, C: URL box). |
| Fetched GitHub | The Projects backend had merged and the repo had been restructured (`app/` to `backend/app/`). Pulled with the owner's approval (fast-forward, so nothing could be lost). | **Yes:** the assumed Projects contract was replaced by the real one; backend commands now run from `backend/`. |
| Landing built | Nav, hero, project rail (real public endpoint), pillars, footer. | - |
| Wording check | The page owner asked whether the text came from the docs. Only the tagline, society name and pillar names are verbatim. | **Yes:** the assistant's earlier statement that it "uses the docs' wording" was overstated. Decision: it is placeholder copy, to be replaced. |
| Docs research | The docs say almost nothing about Landing, and nothing about a footer, team, contact or partners. | We proposed and built a live project count, team section (placeholder names, in the card layout supplied by the owner), join banner and footer; left out what needed content we don't have. |
| Mobile check and quick-win pass | Screenshots at real phone widths showed layout was fine but exposed small tap targets and costly effects. | Blur removed, gradient moved off `fixed`, tap targets at least 44px, arrows hidden on phones, lazy images (§6.2). |
| AI image generator | See the four-step reversal below. | **Yes, twice** (§7). |
| Performance foundations | Route-level code splitting, self-hosted fonts, meta description and `robots.txt`; measured before and after. | The score didn't improve; the finding was that JavaScript is the bottleneck (§6.3). |

**The image-generator reversals, in order:**
1. *First idea:* show AI images on the public gallery. **Rejected**: fresh images took up to ~45 s.
2. *Second:* an authoring tool in the project form that generates, previews and uploads the image, so visitors only see stored thumbnails. **Kept**: this is the final shape.
3. *Third:* calling the image service straight from the browser failed on `localhost`, so we proposed a **backend proxy endpoint**.
4. *Final:* the owner set the rule "nothing that isn't in the backend, the API or the docs". Testing then showed the block was specific to the hostname `localhost` (`127.0.0.1` and real domains work), so we **went back to calling it directly from the browser** and removed the endpoint idea.

### 21 September

| Step | What we did | Changed? |
|---|---|---|
| axios | The assistant proposed replacing axios with `fetch` to save ~16 KiB. | **Withdrawn:** axios is the documented stack and the team's rule (§6.4). |
| Next performance steps | The assistant proposed inlining critical CSS and investigating layout cost. | **Replaced** by a plan built around what visitors actually experience, after we discussed an article on designing for expectation (§6.5). |
| Prefetching and caching | Built page prefetching and a cache of the last project list (§6.6, §6.7). | The "start the request before JavaScript loads" idea was **rejected** because it would bypass axios. |
| Hero before JavaScript | Considered a build-time static hero. | **Deferred:** best done together with the 3D hero, after measuring on the real deployment (§6.8). |
| Documentation | Created the decision log and code guide. | Now updated to cover the whole history, including this timeline. |
| Storage fix | Token handling moved into one module (`tokenStore`) with an in-memory fallback, so the app no longer renders nothing when a browser blocks storage (§1.4). | **Yes:** what we'd logged as a known limitation earlier on 21 Sep is fixed the same day. |
| Small-width audit | Checked 47 states across four viewports, including the OTP screen, edit mode, error messages, landscape phones and very long names and emails. | **Found and fixed** text that couldn't wrap: a real UNILAG-length email overflowed the profile card at 320px (§6.10). |
| Phase 6 research (3D and motion) | Read what the docs say (two lines in the Master Doc plus the design notes) and found the v1 project on the machine to see what the 3D actually was. | **Finding:** v1's "cinematic" landing hero was a scroll-driven Framer Motion animation, not 3D; real 3D was only on v1's Login and Projects pages, and v1 measured a ~940 KB Three.js chunk causing an 11 s+ wait on slow connections. A plan is proposed and waiting on decisions (§6.11). |

### Corrections to statements made earlier
- "Lint is clean": it had one warning (20 Sep).
- "There is no backend to test against": the backend was in the repo.
- "The Landing text uses the docs' wording": only some of it does.
- "Frontend-only image-service calls need a backend endpoint": the block is specific to `localhost`; no endpoint is needed.
- "Replacing axios is the safest big win": it contradicted the documented stack.
- The Lighthouse score didn't improve after fonts and splitting; only first-paint stability and SEO did.

---

## 0. Ground rules and scope

**What we own.** From the Master Task Documentation (§3), the frontend gaps nobody was assigned: the **Auth UI** (Login, Register, OTP), the **Profile page** (view/edit, picture upload) and the **Landing page** (hero, project rail, layout). The doc also lists the Landing **3D/motion polish** and the **performance/code-splitting budget** as unassigned and recommends Ifeoluwa for them — so they need confirming with the team before anyone treats them as ours.

**Rules we set for ourselves** (and why):

| Rule | Why |
|---|---|
| **Stay inside the documented stack and the existing API.** No new backend endpoints. | The project docs and the team's `frontend/CLAUDE.md` define the stack (React, Vite, Tailwind, **Axios**, React Router). Adding endpoints or swapping libraries is the whole team's decision, not ours. |
| **No mock data.** Every screen calls a real endpoint. | The Master Doc §5 names static mock data as v1's biggest failure (Admin and Dashboard). |
| **Every page we build must be reachable and use the real backend route.** | v1 shipped a Profile that called `/hardware/` instead of `/auth/me`. |
| **Where a backend piece doesn't exist yet, build against an *assumed* contract, isolate it in one file, and flag it.** | Lets us finish the frontend without blocking, and makes reconciling later a one-file change (see §9). |
| **Follow `frontend/CLAUDE.md`**: justify every `useEffect`, keep components small, no speculative abstractions, API calls only through `src/api/`. | Team convention. Every effect in the code has a comment saying why it can't be render-time or handler logic. |

**Backend facts we relied on** (checked against the repo, not assumed): responses are always wrapped in `{status, message, data}`, errors included; `verify-code` *consumes* the OTP and `register` only accepts a code that was already consumed; `PUT /auth/me` accepts only `full_name, department, level, bio, profile_image_url`; `GET /projects` is public and paginated.

---

## 1. API layer and session

### 1.1 One typed client that unwraps the envelope
- **Decision:** All requests go through one Axios instance (`src/api/client.ts`). Endpoint functions in `src/api/*.ts` return plain typed data; a small `unwrap()` removes the `{status,message,data}` wrapper.
- **Why:** Pages never deal with the envelope, and `CLAUDE.md` forbids importing axios in components. Types in `src/types/` mirror the backend schemas (with a "keep in sync" comment).
- **Trade-off:** The types are written by hand, so they can drift from the backend. Generating them from the backend's OpenAPI schema would be more robust; it wasn't set up.

### 1.2 Silent token refresh
- **Decision:** A request interceptor attaches the access token. A response interceptor, on a `401`, refreshes once and retries the request. Only **one** refresh runs at a time — other requests that fail meanwhile wait for the same promise. Login, register, refresh and the OTP endpoints are excluded, because a `401` there means "wrong credentials", not "expired token".
- **Why:** Matches the docs' "Axios interceptor pattern" and avoids a stampede of refresh calls.
- **Verified:** three parallel expired requests produced exactly one refresh call; a wrong password never triggered a refresh or redirect.

### 1.3 Session expiry drops the user instead of redirecting *(deliberate deviation from the docs)*
- **Decision:** When refresh fails, the client clears the tokens and calls a registered handler (`setSessionExpiredHandler`) that empties the user in `AuthProvider`. `ProtectedRoute` then redirects protected pages to `/login`.
- **Why:** The docs say "redirect to login". We first did that with a hard redirect and found it also bounced **public** pages: a visitor with stale tokens opening the Landing page was thrown to `/login`.
- **Trade-off:** Slightly more moving parts (a callback), but public pages stay public.
- **Verified:** stale tokens on `/` keep the visitor on Landing and clear the tokens; a session dying on `/profile` redirects to login.

### 1.4 Tokens live in browser storage, through one module
- **Decision:** access and refresh tokens are kept in `localStorage`, but only `src/api/tokenStore.ts` touches them. The API client and `AuthProvider` both call it.
- **Why:** the docs prescribe local storage ("the frontend stores the tokens locally") and the backend returns tokens in the response body (no cookies). One module also removes the duplicated key names that used to be spread across two files.
- **Trade-off:** any script injection (XSS) could read the tokens; httpOnly cookies are safer but need backend changes. This is why user-supplied links are guarded (§4.2).
- **Changed on 21 Sep:** we had logged a *known limitation*: if a browser blocked storage entirely, the whole app rendered nothing, because the login code read storage at startup without protection (a test showed this predated the projects cache). `tokenStore` now falls back to **memory** when storage throws, so the app renders and login works for as long as the tab is open; the session is then not remembered after a reload, which is the honest behaviour for a browser that won't allow storage.
- **Verified in a real browser:** normal login persists under the same keys and survives a reload; logout clears both tokens; bad tokens are cleared and the user is sent to login; with storage blocked, Landing renders its projects, login works and reaches `/profile`, and a reload returns to login.

### 1.5 Show the backend's own error message
- **Decision:** `errorMessage(error, fallback)` returns the backend's `message` when the error carries one, else a fallback (network failure etc.).
- **Why:** "Email already registered" or "Account is inactive" is far more useful than a generic failure. Login used to say "Invalid email or password" for everything.

### 1.6 Dev proxy now, deploy address later
- **Decision:** In development, Vite proxies `/api` to `localhost:8000`, and the client uses a relative `/api/v1`.
- **Trade-off / deferred:** The docs say production reads the API host from `VITE_API_URL` (Vercel frontend, Render backend). That isn't wired yet — the client must read it before any real deployment, and the backend's `CORS_ORIGINS` must include the frontend's address (§9).

---

## 2. Auth UI

### 2.1 Register is one page with three steps
- **Decision:** `Register` owns the state and moves through *details → OTP → create account*; `OtpVerification` is its second screen. After the account is created the user is logged in automatically.
- **Why:** The backend requires an OTP verified *before* register. Auto-login means registration ends on an authenticated session instead of dropping the user on a second login form.

### 2.2 The burned-code trap (found and fixed)
- **What we found:** `verify-code` uses the code up, but the password rule (8+ characters) and the duplicate-email check only run at `register`. A short password or an already-used email failed **after** the code was burned; the OTP screen then said "Invalid or expired code" and the user was stuck.
- **Decision:** On a register failure, return to the details step with the **backend's real message**, keep what the user typed, and request a fresh code on continue. The password field also enforces 8 characters in the browser.
- **Why:** This is exactly the gap between a *requirement* (register works) and an *expectation* (I can fix my mistake).
- **Verified against the live backend:** duplicate email → back on details, message shown, inputs preserved.

### 2.3 Login redirects by role
- **Decision:** `redirectPathForRole` sends ADMIN to `/admin` and everyone else to `/profile` (Master Doc §3.1).
- **Known gap:** there is no `/admin` page yet (Ifeoluwa's). Until then, admins see the "Page not found" page — deliberately not a blank screen.

### 2.4 Auth state
- **Decision:** `AuthContext` (the type and context) and `AuthProvider` (the logic) are separate files; `useAuth()` is the only way components read it. `updateProfile()` replaced an unused `refreshUser()`, because `PUT /auth/me` already returns the updated user, so a second `GET` is wasted.
- **Why:** The split satisfies the fast-refresh lint rule. Components depend on `useAuth`, not on the API directly.

### 2.5 Small shared pieces
- `TextField` is shared by Login, Register, OTP and Profile (the "used on 2+ pages → shared component" rule). `ProtectedRoute` waits for the session to restore before deciding.
- **Note:** the backend returns the OTP in the send-code response (`debug_code`) and the UI doesn't show it, because Brevo email isn't wired yet. Until it is, real people can't complete registration through the UI (§9).

---

## 3. Profile

- **Reads `/auth/me`.** The page reads the user from `useAuth()`, which is filled from `GET /auth/me` — never `/hardware/` (the v1 bug).
- **Edit sends only changed fields.** `PUT /auth/me` applies exactly what it receives, and `full_name` / `department` are `NOT NULL` in the database — sending `null` would 500. So we trim, block blank values before sending, and skip the request entirely when nothing changed.
- **`level` may be `""` or `null`** (registration sends `""`), so the page treats both as empty.
- **Picture upload** uses `uploadImage()` then saves the returned URL via `updateProfile`. It works against an **assumed** `/upload/image` contract (§9). Until that endpoint exists the picker shows a friendly error instead of breaking.
- **Log out lives here** — the only place a user can sign out.
- **Structure:** `Profile` (shell, view/edit toggle), `ProfileDetails`, `ProfileEditForm`, `ProfileAvatar`. The bio textarea is inline in the edit form because only Profile uses it; extract it if another page needs one.

---

## 4. Landing page

### 4.1 What the docs specify — and what they don't
The Master Doc's whole requirement is "hero section, project showcase rail, overall layout", plus the note that this is the page **demoed to the SEES president**. The design doc adds the dark/cinematic tone and a Netflix-style horizontal project rail. **Nothing** in either document specifies a footer, contact links, team section, partners or exact copy, so those are our proposals (§4.4).

### 4.2 The project rail
- **Real data.** It reads the public `GET /projects` (latest 12). It has four states — loading skeleton, error, empty ("No projects yet") and data — so a failure never looks like an empty gallery.
- **Cards don't link to a detail page yet.** That route (`/projects/:id`) belongs to Emmanuel's Projects frontend and doesn't exist; a link would land on "Page not found".
- **Security: only `http(s)` links are rendered.** Demo/GitHub URLs are typed by users and the backend accepts any string. A `javascript:` URL would run script on click, so anything else is dropped. Tested with a real `javascript:alert(1)` value.
- **Live count** ("N projects showcased") comes from the API's `total`, so it needs no extra request.
- **Kept simple:** the rail uses native scroll-snap. On phones the arrows are hidden (swiping works); on tablet and up they scroll by 80% of the rail.

### 4.3 Sections beyond the spec
Nav, hero, rail, three-pillar strip, team section, join banner (hidden when signed in — pitching sign-up to someone with an account is noise) and footer. Team cards follow the layout supplied by the page owner: photo area on top or an outlined user icon, name and uppercase role below. The **team content is placeholder** (fake names, no photos); photos go in `public/team/` via `imageUrl`.

### 4.4 Copy is placeholder
Only "New Semester, New Heights", the society's name and the three pillar names are verbatim from the docs; the pillar descriptions are stitched from doc phrases; the headline ("The digital home of SEES engineering."), the rail subtitle, button labels and CTA text are ours. The team agreed to replace them later. The meta description is the docs' own summary sentence.

### 4.5 Not built because the docs give nothing to build from
Contact/social links, partners and sponsors, a list of executives. (The Master Doc lists the dev team only as internal task assignments, not as public credits.)

---

## 5. Look and feel

- **Decision:** the SEES v1 palette and fonts are ported into Tailwind v4's CSS-based `@theme` in `index.css` (forest, mint, mustard, teal, void, gradients, shadows).
- **Why / status:** no design tokens existed in the repo. The docs' design table lists three tokens — `#000F0D`, `#A7FFEB`, `#E4A11B` — which match ours; the extras (forest, teal, gradients) come from v1 and are unconfirmed. Ifeoluwa owns the official tokens and Apena the shared `Button`; button styles are currently repeated inline and should be swapped for the shared component when it ships.

---

## 6. Performance and mobile

### 6.1 The requirement
The priority is **very fast pages, smooth scrolling, and good phone and tablet layouts**. Because "fast" is easy to claim and hard to prove, every change below was **measured before and after**, and where a result didn't improve we say so.

### 6.2 Quick-win pass (21 Sep) — measured
| Change | Why |
|---|---|
| Removed the 20px `backdrop-blur` from every card | It was invisible over the opaque gradient but costly on phones, especially inside a scrolling rail. |
| Moved the page gradient from `background-attachment: fixed` to a `body::before` fixed layer | `fixed` backgrounds repaint every scroll frame on many mobile browsers. |
| All tap targets ≥ 44px (Landing **and** Auth/Profile) | Phone usability; several were 17–42px. |
| Rail arrows hidden on phones | Swiping works; the arrows squeezed the heading onto two lines. |
| `loading="lazy"`, `decoding="async"` and dimensions on images | Faster first load, no layout shift. |

**Result** (scripted scroll on an emulated 390px phone, 4× CPU slowdown): average frame time **26.7 → 16.7 ms** (steady 60fps), frames slower than 33 ms **11–14 → 0–1** per pass, worst frame **83 → 33 ms**, layout shift 0.0027 → 0.0003. A real-browser audit of `/`, `/login`, `/register`, `/profile` at 320/390/820 px found **0 targets under 44px, 0 horizontal overflow, 0 blur elements**. *(Software rendering, so the direction is reliable, the exact numbers aren't.)*

### 6.3 Foundations — measured, and honest about the result
**Changes:** route-level code splitting (Login, Register, Profile load on demand; Landing stays in the main bundle); fonts **self-hosted** (`@fontsource` packages: Inter variable + JetBrains Mono regular) instead of Google Fonts; a meta description and `robots.txt`.

**Lighthouse, mobile profile, production build served with compression and long-lived caching, 5 runs each:**

| | Before | After |
|---|---|---|
| Performance | 85–95 (median 90) | 83–91 (median 87) |
| First paint | 1.89–2.99 s | **1.89–1.91 s** |
| SEO | 82 | **100** |
| Accessibility / best practices | 100 / 100 | 100 / 100 |
| Transferred / requests | 183 KB / 8 | 170 KB / 7 |

**What this tells us:** the score didn't improve (the ranges overlap; runs on one build vary ±4). What did improve is **predictability** — first paint no longer swings because of a third-party font request — and SEO. The real bottleneck is **JavaScript, not the network** (the server answers in ~18 ms): the page is drawn by the browser, so nothing appears until the bundle downloads and runs. The bundle is ~89 KiB compressed: React + ReactDOM ~57, axios ~16, router ~14, our code ~6. Splitting saved little now because our pages are tiny (under 2 KB each); it is the foundation for the 3D work.

### 6.4 We are keeping axios *(decision reversed)*
We proposed replacing axios with the browser's `fetch` to save ~16 KiB. We withdrew it: **axios is the documented stack** (and `CLAUDE.md` requires API calls through the shared axios client), so swapping it is the team's decision. *Lesson recorded: flag any deviation from the documented stack before proposing it.*

### 6.5 Thinking in moments, not scores
We reviewed an article on designing for **expectation, not just requirement** ("Make it feel instant"). It reframed the plan: list the *moments* a visitor experiences and improve when the work happens, instead of only chasing scores.

| Moment | What we do |
|---|---|
| First view of the site | Show the hero before JavaScript loads — **deferred** (6.8). |
| Seeing the projects | Remember the last result so returning visitors see cards on first paint (**done**, 6.7). |
| Tapping "Log in" | Download the auth pages ahead of time (**done**, 6.6). |
| Signing in | Start downloading the Profile page while the login request runs (**done**, 6.6). |
| Waiting for an image | Let the author keep working while it generates (guidance for the project form, §7). |

### 6.6 Prefetching the auth and profile pages (done)
- **Problem we created:** splitting the code made "tap Log in" wait for a download, with a blank screen meanwhile.
- **What it does:** (a) after Landing loads, the browser downloads the three pages while **idle**; (b) hover, touch or keyboard-focus on a link downloads that link's page first (`PrefetchLink`); (c) submitting login/register starts the Profile download **in parallel** with the request.
- **Details:** a timer stands in for `requestIdleCallback` on Safari (which lacks it); the idle download is **skipped when the visitor has data saver on** (hover still works). Costs about 5 KB for visitors who never sign in.
- **Trade-off:** a failed prefetch is ignored and the real navigation simply retries. It only helps navigation from Landing — a direct visit to `/login` or `/profile` (bookmark, refresh) still downloads the main bundle then the page, one after the other (§9).
- **Verified in a real browser** on the production build: A) all three pages fetched with no click, and clicking "Log in" needed **0** new downloads; B) the Safari-style fallback works; C) with data saver, nothing prefetched at idle but hover fetched the page; D) at login the Profile code was requested **before** the login and user-lookup requests, and the login ended on `/profile`; E) the same at registration (between verify-code and register).

### 6.7 Remembering the last project list (done)
- **What it does:** after a successful load, the list (12 projects) is saved in the browser (`sees.projects.v1.12`). On the next visit it shows immediately; the fresh list from the API always replaces it. A refresh that **fails** leaves the cached cards instead of flipping to an error.
- **Safeguards:** copies older than 7 days, unreadable JSON and wrongly-shaped data are ignored; a version in the key lets us invalidate old copies if the project shape changes; blocked or full storage is tolerated.
- **Trade-offs:** a deleted project can show briefly on a repeat visit (harmless for a public gallery that changes weekly); if the server is unreachable a stale list is shown silently. Only public data is stored.
- **Rejected: the "fetch exception".** Starting the request before the JavaScript loads needs the browser's plain `fetch` in `index.html`, i.e. **bypassing axios** for one call. We chose not to, per §6.4; the gain would have been roughly 0.3–0.5 s, for first-time visitors only.
- **Verified in a real browser** by delaying or failing the API: first visit shows the skeleton, then 4 cards and writes the cache; a repeat visit shows the 4 cards **while the request is still pending**; when the server data changed, the stale list showed first, then updated (5) and refreshed the cache; API down with a cache → cards stay, no error; API down without a cache → error state; corrupt, wrongly-shaped and expired caches were all ignored.

### 6.8 Deferred: hero before JavaScript (was "Item 1")
- **Idea:** generate the hero's HTML at build time so it appears before the JavaScript loads. It's the biggest first-paint win (estimated ~0.7–1.0 s vs ~1.9 s on the throttled test — an estimate, not a measurement).
- **Why deferred:** it needs a custom build step the whole team inherits, behaves differently in dev and production, and could make blocking time look worse. Our scale doesn't demand it (a small society, mostly cheap phones — the benefit is per-visitor speed, not server load), and the wording is still placeholder. **Do it together with the Phase 6 3D hero**, which needs the same static "poster", and measure on the real deployment first.

### 6.9 Observations worth knowing
- The bundler put axios and the API client in their own shared file, loaded at startup next to the main file. Total JavaScript is unchanged (~106 KB compressed for Landing).
- If the production backend is on a free Render plan, a sleeping server can take tens of seconds to answer the first request — that would outweigh every frontend optimisation. Worth confirming the plan with whoever deploys.

### 6.10 Small-width and awkward-content audit (21 Sep)
- **What we checked:** 47 states in a real browser (production build) across 320px, 390px, 820px and a landscape phone (844x390): Login (plain and with an error), Register (details, the OTP screen, an OTP error), Profile (view, edit, edit with an error, an upload error), a Profile with a very long unbroken name, email, department and bio, and Landing with a very long unbroken project title, description and tech tag. For each: horizontal overflow, text spilling out of its box, and any tap target under 44px.
- **What we found:** the layouts were sound and every tap target passed, but **text that can't wrap** overflowed. A 45-character name caused horizontal scrolling of the whole page (up to 736px at 320px), and an email overflowed the profile card. This isn't only a test artefact: a real UNILAG email such as `230408018@live.unilag.edu.ng` is about 215px wide, while the profile card's inner width at 320px is only 190px. The email on the OTP screen and long project titles were affected in the same way.
- **Fix:** Tailwind's `wrap-anywhere` (breaks a word only when it would otherwise overflow) on the places that show user-entered or database text: the profile name, all profile detail values, the OTP screen's email, and the project card's title, description and tech tags. Ordinary text still wraps at spaces as before.
- **Result:** the same 47 states now report **0 overflow, 0 spilling text, 0 small tap targets**, and screenshots at 320px confirmed the wrapped name, email and OTP text.
- **Convention going forward:** any element that displays text a user or the database supplied should wrap (see CODE_GUIDE §5).

### 6.11 Phase 6 (3D and motion): what the docs say, what v1 did, and the proposed plan
**What the documents actually say.** Very little:
- *Master Task Doc §3.9:* "Frontend: 3D/motion polish (Phase 6) - Framer Motion + React Three Fiber elements, isolated so they don't affect other pages' load performance (§10)". Owner: unassigned.
- *Master Task Doc §3.15:* "Performance budget / code-splitting the 3D deps away from Dashboard/Admin/Hardware - Landing page's Three.js/Framer weight doesn't slow down other routes (§10 requirement)". Owner: unassigned. The Master Doc's own recommendation table suggests **Ifeoluwa** for the 3D/motion and the performance budget.
- *Documentation.md:* React Three Fiber / Drei / Three.js "powers the cinematic gallery and hero experiences"; "3D composition for key moments such as the landing page hero and the project showcase"; Framer Motion for "entrances, hover states, modal transitions, and state changes"; and the rules: keep the dark, technical, cinematic tone, keep motion purposeful, prefer readable contrast over decorative complexity.
- **Not available:** "§10" and the definition of "Phase 6" live in the Technical Documentation, which is not in the repo or the shared files. There is **no design brief** (what the scene is, what it shows) and **no numeric performance budget** anywhere we can read.

**What v1 did (the v1 project is on this machine).**
- The v1 landing hero was **not 3D**. It was a scroll-driven **Framer Motion** effect: a 200vh section with a pinned viewport, where a small "circuit via" ring with eight radiating traces expands into a circular mask that reveals a tech-grid background and marquee rows of engineering topics (Embedded Systems, VLSI, IoT, Robotics...). The unused marquee animation tokens in our theme come from this.
- v1's **real 3D** (React Three Fiber) was on the **Login** page (a background scene) and the **Projects** page (a full-screen canvas of floating 3D project cards with orbit controls and stars) - the "project showcase" the docs mention, which in v2 belongs to Emmanuel's Projects page.
- v1 had a **performance problem**, documented in its own code comments: the Three.js stack was about **940 KB** inside the Login/Register chunk, which meant an **11 s+ wait** on a slow connection, and it needed a prefetch workaround. This is exactly the motivation for the "isolate it" requirement.
- v1 landing content that can be reused if the team agrees: the hero copy ("Innovating from Akoka to the world", "Global Hub for SEES Engineering"), the marquee topics, and a WhatsApp community link for the footer. v1's stats bar was **hard-coded placeholders**, so it must not be ported as it was (Master Doc §5: no static stats).

**Proposed plan** (three independent layers, each measured before it ships):
1. **Motion foundation** (Framer Motion, in the documented stack): load it lazily (`LazyMotion`) so it costs almost nothing up front; entrances on scroll, card hover elevation; everything switched off for `prefers-reduced-motion`.
2. **Cinematic hero:** port v1's scroll-driven circuit reveal, redesigned to animate only compositor-friendly properties (transform and opacity) and to pause the marquee until it is revealed, because animating a clip-path over a full-screen element is costly on phones. This layer is 2D and cheap.
3. **Real 3D (optional, enhancement only):** a small React Three Fiber scene in the hero, loaded as its **own chunk after the page is interactive**, only when the device qualifies (not a phone by default, WebGL available, no reduced-motion, no data saver, not a slow connection), with rendering paused when off-screen or the tab is hidden, a capped pixel ratio, and a static poster everywhere else. It must never load on any other route. The project-showcase 3D is Emmanuel's page and would reuse the same lazy wrapper.
4. **Budget and gating:** a shared "can this device afford rich effects" check used by layers 1-3, and written budgets: eager JavaScript growth kept to a few KB, the 3D chunk capped and never fetched off Landing, Lighthouse mobile not worse than today with the effects deferred, layout shift 0, and scroll frame time on an emulated phone kept at 60 fps.

**Decisions needed before building** (asked of the page owner): the hero concept (port v1's reveal, or design a new 3D hero), how much real 3D (none for now, a hero accent, or also the showcase), whether to reuse v1's hero copy and footer link, and confirmation of ownership with the team (the Master Doc suggests Ifeoluwa). If the Technical Doc's §10 and Phase 6 text can be shared, the budget numbers should follow it.

---

## 7. AI image generator

### 7.1 The idea
Authors generating a project thumbnail from a topic (using Pollinations, as v1 did). It is **not in the project docs** — it's an addition that lives in Emmanuel's create/edit project form and needs coordinating with him.

### 7.2 What we measured before designing it
A fresh prompt took ~45 s in early tests and 4–5 s later (very variable), sometimes failing with a 500; an already-generated image is cached and returns in ~0.7 s. So generating on the public gallery is out: **visitors only ever see the stored thumbnail**, uploaded through `/upload/image`; the generator runs only while an author creates a project. Cards without a thumbnail keep the instant category placeholder.

### 7.3 Backend proxy considered and rejected
Calling Pollinations from the browser first **failed on `localhost`** — the service returns `403 Missing Turnstile token` for exactly that hostname, while `127.0.0.1`, normal domains and the docs' production address all work. That made a backend proxy tempting, but we rejected it: it needs a **new backend endpoint** (against §0), and a shared server IP would also hit Pollinations' per-IP limit (anonymous: one queued request per IP), where each author's own browser has its own. **Decision: call Pollinations directly from the browser; store the result through the existing upload endpoint.**

### 7.4 Limits to know
- In development, open the app at **`http://127.0.0.1:<port>`**, not `localhost` (`npm run dev -- --host 127.0.0.1`).
- Production should work on a normal domain, but isn't verified until deployed, and the service could change its anti-bot rules.
- Anonymous images carry a small **"pollinations.ai" watermark**, and quality is generic. A paid API key might help but would be public in browser code.
- The description the author types is sent to a third party; the UI says so.

### 7.5 The component
`ImageGenerator`: topic box → Generate → spinner with **Cancel** (90 s timeout) → 16:9 preview → **Use this image** (uploads, then hands the stored URL to the form) or **Generate again** (fresh seed). Failures keep the previous preview; a failed upload keeps the image for retry. It does **not** lock the host form, so authors can keep working while it generates. The brand style is added to the prompt for consistent thumbnails.

### 7.6 Temporary sandbox
`pages/dev/ImageGeneratorPreview.tsx` (route `/dev/image-generator`, compiled out of production builds) exists only so the component could be tried before Emmanuel's form exists. **Delete it when a real form uses the component.**

---

## 8. How we verified things

The repository has **no test runner**, so verification used throwaway scripts kept **outside the repo** (nothing committed): a simulated browser (jsdom) against the live backend for behaviour, headless Edge driven over the DevTools protocol for real-browser checks (device emulation at 320/390/820/1280 px, network interception, screenshots), and Lighthouse for performance (at least 5 runs, comparing medians). The layout checks are scripted audits (overflow, spilling text, tap targets) run over many states and viewports, not just screenshots.

**Trade-off:** none of those checks persist, so regressions won't be caught automatically. We recommend adding **Vitest** (component and hook tests) and **Playwright** (browser flows) — Apena's smoke-test task is the natural home. Also worth remembering: `--screenshot` in headless Edge has a ~500px minimum window and full-page captures paint fixed backgrounds white; both looked like bugs and weren't.

---

## 9. Open items and deferred work

| # | Item | Owner / dependency | State |
|---|---|---|---|
| 1 | `/upload/image` — real request/response shape | Zafrullah's endpoint | **Assumed**: multipart `file` → envelope `data: {url}`. Fix only `src/api/upload.ts` when confirmed. Profile picture and the image generator depend on it. |
| 2 | `/admin` page | Ifeoluwa | Admin login lands on "Page not found" until it exists. |
| 3 | Deployment address (`VITE_API_URL`) and CORS | Henry / whoever deploys | Not wired; needed before any real deploy. Also confirm the Render plan (cold starts). |
| 4 | OTP by email (Brevo) | Henry | Backend only returns `debug_code`; real users can't register via the UI until email works. |
| 5 | Project detail route to link rail cards to | Emmanuel | Cards intentionally don't link yet. |
| 6 | Design tokens / shared Button | Ifeoluwa / Apena | Our theme matches the docs' 3 tokens; extras unconfirmed; inline button styles to be swapped. |
| 7 | Phase 6 3D / motion + performance budget | Unassigned in the Master Doc (it suggests Ifeoluwa); the Technical Doc's §10 is not available | Researched, plan proposed, waiting on decisions (§6.11). Must be lazy-loaded and skipped on phones, reduced-motion and data-saver. Pair with 6.8. |
| 8 | Hero before JavaScript | Us, later | Deferred (6.8). |
| 9 | Direct visits to `/login`, `/profile` need two sequential downloads | Us | Side effect of splitting; not covered by prefetching. |
| 10 | Team section content, all placeholder copy, contact/social/partners | The team / SEES | Fake names and no photos; wording to be replaced. |
| 11 | Image generator: host form, watermark, production check | Emmanuel / us | Component built; sandbox page to delete. |
| 12 | Hardware backend | Olaiwon | On an unmerged branch; not ours. |
| 13 | Persistent tests | Apena / team | None in the repo (§8). |
| 14 | Minor: logged-in users can open `/login` and `/register`; optional `level` is sent as `""` | Us | Not fixed. |

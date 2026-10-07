# SEES Nexus frontend — code guide

How the frontend is built and how to work in it.

## 1. Run it

```bash
# backend (from backend/, see backend/README.md): SQLite works with no setup
python seed.py                      # optional: creates admin@seesnexus.dev and student@seesnexus.dev, password ChangeMe123
uvicorn app.main:app --reload       # http://localhost:8000

# frontend (from frontend/)
npm install
npm run dev                         # http://localhost:5173  (proxies /api to localhost:8000)
npm run dev -- --host 127.0.0.1     # use this instead when trying the AI image generator (the service blocks the hostname "localhost")
```

Checks to run before sharing work (all three must be clean):

```bash
npx tsc -b      # type check
npx oxlint      # lint
npm run build   # production build
```

**Stack:** React 19, TypeScript, Vite, Tailwind CSS v4 (CSS-based theme, no `tailwind.config.js`), React Router, Axios.

## 2. Folder map

```
src/
  main.tsx                     entry: StrictMode → QueryClientProvider → BrowserRouter → AuthProvider → App
  App.tsx                      the route table only (Landing eager; other pages lazy)
  index.css                    Tailwind import, self-hosted fonts, theme tokens, page background
  routes/pageLoaders.ts        how each lazy page (and the AppLayout) is loaded + prefetch helpers
  layouts/
    AppLayout.tsx              the sidebar frame around every signed-in page (§3.11)
    sidebar/navItems.ts        every sidebar link, grouped; add a link here when its page exists
    sidebar/SidebarNav.tsx     the grouped links (expanded or icons-only)
    sidebar/UserMenu.tsx       the signed-in person + Profile / Log out menu
  api/
    client.ts                  the shared Axios instance, interceptors, unwrap(), errorMessage(), isNotFoundError()
    auth.ts                    login, register, sendCode, verifyCode, getMe, updateMe
    projects.ts                listProjects, getProject (public); createProject, updateProject, deleteProject
    hardware.ts                listHardware, getHardware (public); requestLoan, listMyLoans, returnLoan
    queryClient.ts             the shared TanStack Query cache and its defaults
    queryKeys.ts               the name of every cached API read (used to refresh lists after changes)
    tokenStore.ts              the only code that reads/writes the session tokens (memory fallback if storage is blocked)
    upload.ts                  uploadImage (assumed /upload/image contract)
    imageGeneration.ts         generateImage (calls the image service directly)
  types/                       hand-written types mirroring the backend schemas (auth, project, hardware, envelope)
  context/
    AuthContext.ts             the context + its value type
    AuthProvider.tsx           session state and actions (login, logout, updateProfile)
    ToastContext.ts / ToastProvider.tsx   the toast messages (showToast) and where they render
  hooks/
    useAuth.ts                 the only way components read the session
    useShowcaseProjects.ts     Landing's rail (useQuery + a remembered copy, §3.5)
    useProjectList.ts          a page of projects with filters (Projects page)
    useProject.ts              one project (shows a list's copy instantly, §3.12)
    useCreateProject.ts / useUpdateProject.ts / useDeleteProject.ts   changes; each refreshes the lists
    useUrlFilters.ts           filters + page in the address bar, shared by list pages (§3.13)
    useHardwareList.ts         a page of hardware with filters
    useMyLoans.ts              the signed-in person's loans (off for visitors)
    useHardwareNames.ts        names of the items loans point to (temporary, §3.13)
    useRequestLoan.ts / useReturnLoan.ts   loan actions
    usePrefetchAuthPages.ts    idle prefetch of the auth pages
    useToast.ts                the only way components show a toast
    useModalDialog.ts          opens/closes a native <dialog> as a modal (Modal + the phone drawer)
  components/                  shared UI, one folder each, default export from index.tsx
    Button/ (+ buttonClassName.ts)  Card/  Badge/  Spinner/  Skeleton/  EmptyState/  ErrorState/
    Pagination/  Modal/  ConfirmDialog/  Field/ (+ fieldStyles.ts)  TextField/  TextArea/  Select/
    Avatar/  ProtectedRoute/  AdminRoute/  PrefetchLink/  ImageGenerator/  ProjectCard/   (see §3.10)
  pages/                       one folder per route-level feature, named exports
    landing/   Landing, LandingNav, HeroSection, ProjectShowcaseRail,
               PillarsSection, TeamSection, JoinSection, LandingFooter
    auth/      Login, Register, OtpVerification
    profile/   Profile, ProfileDetails, ProfileEditForm, ProfileAvatar
    projects/  ProjectsList, ProjectDetail, NewProject, EditProject, ProjectForm, TechStackInput,
               ProjectNotFound, projectFormValues (values, limits, validation)
    hardware/  HardwareList, HardwareCard, LoanRequestModal, cardActionId
    loans/     MyLoans, LoanCard
    notfound/  NotFound
    dev/       ImageGeneratorPreview, ComponentsPreview  (temporary sandboxes, dev builds only)
  utils/       redirectPathForRole, projectLabels, hardwareLabels (labels, select options, badge tones, URL checks),
               isHttpUrl, canEditProject
public/        favicon, icons, robots.txt
docs/          this guide and the decision log
```

## 3. How the pieces connect

### 3.1 Making an API call
```
component / hook  →  src/api/<thing>.ts  →  client.ts (axios)  →  backend
      ▲                    unwrap() removes {status, message, data}          │
      └──────────── plain typed data (e.g. User, PaginatedProjects) ◄────────┘
```
An endpoint function looks like this — one line, typed, no envelope in sight:

```ts
export function getMe() {
  return unwrap<User>(api.get("/auth/me"));
}
```
Errors: `errorMessage(error, "fallback text")` returns the backend's own message when it sent one.

### 3.2 The session (`AuthProvider` + `client.ts`)
- **On app start**, if a token is stored (read through `tokenStore`), `AuthProvider` calls `GET /auth/me`. While that runs `isLoading` is true, so `ProtectedRoute` waits instead of redirecting a signed-in user.
- **Login** stores both tokens, then calls `/auth/me` and puts the user in state. `redirectPathForRole` decides where to go.
- **An expired access token:** the response interceptor sees a `401`, asks `/auth/refresh` for a new token (only **one** refresh runs at a time; other failing requests wait for it), then retries the original request.
- **A dead refresh token:** the client clears the tokens and calls the handler `AuthProvider` registered, which empties the user; `ProtectedRoute` then redirects to `/login`. Public pages are untouched.
- **Blocked storage:** `tokenStore` keeps the tokens in `localStorage`; if the browser throws on every storage call it falls back to memory, so the app still renders and login works until the tab closes.
- *Known caveat:* the refresh call uses its own hard-coded `/api/v1/...` path; update it when `VITE_API_URL` is added.

### 3.3 Pages load on demand
`routes/pageLoaders.ts` is the single place that says how each lazy page is loaded:

```ts
export const pageLoaders = {
  login: () => import("../pages/auth/Login"),
  register: () => import("../pages/auth/Register"),
  profile: () => import("../pages/profile/Profile"),
};
```
`App.tsx` renders them through `React.lazy`, and `prefetchPages()` calls the **same** imports early so the browser already has the code when the route opens. Three things trigger it: `usePrefetchAuthPages` (browser idle after Landing loads, skipped on data saver), `PrefetchLink` (hover / touch / focus), and the login/register submit handlers (start the Profile download while the request runs).

### 3.4 Loading data from the API (TanStack Query)
Every API **read** a page needs on load goes through TanStack Query's `useQuery`, wrapped in a hook under `src/hooks/`. It sits on top of our axios functions; it does not replace them.

```ts
export function useSomething(id: string) {
  return useQuery({
    queryKey: queryKeys.something.detail(id),   // its name in the cache
    queryFn: () => getSomething(id),             // the plain function from src/api/
  });
}
```
What we get for free: one request even if two components ask for the same data, loading/error flags, a quiet refresh when you come back to a page, and one retry on network or server errors (never on a 4xx, which would just fail again). Defaults live in `api/queryClient.ts` (data counts as fresh for 30 s).

- **After a change** (create/edit/delete), refresh what it affected: `queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })`. Keys are nested, so `["projects"]` also refreshes every list and detail under it. Name every key in `api/queryKeys.ts`, never inline.
- **On login, logout and session expiry** `AuthProvider` empties the whole cache, so one person's private data (their loans, the admin's user list) never shows to the next person on a shared computer.
- The signed-in user is **not** in the query cache; it stays in `AuthProvider` (§3.2).

### 3.5 The project rail (`useShowcaseProjects`)
```
first render:  readCache() ── found & fresh (≤ 7 days)? ─► show those cards immediately (marked stale)
                        └── else ► skeleton
at once:       useQuery → GET /projects?page_size=12
                 ├─ success ► show fresh list + write it to the cache
                 └─ failure ► keep cached cards if we have them, otherwise the error state
```
The saved copy is handed to `useQuery` as `initialData` with its real save time, so it is shown instantly but refreshed straight away. The cache key is `sees.projects.v2.<pageSize>`. Bump the version if the `Project` type changes. Landing's rail shows four states: loading skeleton, error, empty, data.

### 3.6 The AI image generator (`ImageGenerator`)
`topic → generateImage()` (image service) → preview from an object URL → **Use this image** → `uploadImage()` (`/upload/image`) → `onUploaded(url)` to the host form, which stores it as the project's `thumbnail_url`. It can be cancelled, times out after 90 s, keeps the previous preview when a new attempt fails, and revokes its object URLs when replaced or unmounted.

### 3.7 Registration and login
```
Register (details) --sendCode(email)--> OtpVerification --verifyCode(email, code)--> onVerified(code)
     ^                                                                                    |
     |  any failure: back to the details step with the backend's message                  v
     +------------------------------------------------ register({...details, code}) --> login() --> GET /auth/me --> redirectPathForRole(role)
```
- `verify-code` **uses the code up**, and `register` only accepts an already-used code. That is why a failure at the register step sends the user back to the details form to request a fresh code, instead of leaving them on the OTP screen.
- `Register` owns the state (`details`, `step`, `error`, `isSubmitting`); `OtpVerification` only shows the second screen.
- **Login** calls `login(email, password)` from `useAuth()`: the provider stores both tokens, calls `/auth/me`, and returns the user so the page can navigate by role (ADMIN to `/admin`, everyone else to `/profile`).
- Both the login submit and the register "code verified" handler call `prefetchPages("profile")` first, so the Profile code downloads while the request runs.

### 3.8 Profile view and edit
- `Profile` reads the user from `useAuth()` (filled from `GET /auth/me`) and holds one piece of state: `isEditing`. It composes `ProfileAvatar`, then either `ProfileDetails` (read-only) or `ProfileEditForm`, and has the **Log out** button.
- `ProfileEditForm` keeps a *draft* of name, department, level and bio. On save it trims the values, refuses blank name/department, and builds `changes` containing **only fields that differ** from the current user. No changes closes the form without a request; otherwise `updateProfile(changes)` runs `PUT /auth/me` and the provider replaces the user with the response.
- `ProfileAvatar`: pick a file, `uploadImage(file)` returns a URL, then `updateProfile({ profile_image_url })`. A failed upload shows a message and leaves the current photo.

### 3.9 How Landing is put together
`Landing` only composes: `LandingNav`, then in `<main>` `HeroSection`, `ProjectShowcaseRail`, `PillarsSection`, `TeamSection`, `JoinSection`, and `LandingFooter`. The nav, hero, join banner and footer are **auth-aware** (`useAuth()`): signed-out visitors see Log in / Register / Get started, signed-in users see Profile links and no join banner, and nothing is shown while the session is still being restored.

| Element | Phone (under 768px) | Tablet and up |
|---|---|---|
| Hero headline | smaller text | larger text |
| Project rail | swipe; arrows hidden | arrows visible (44px) |
| Pillars | stacked | three columns |
| Team | 2 x 2 | 4 across |
| Footer | stacked | three columns |

`Landing` also calls `usePrefetchAuthPages()`. Project cards render only `http(s)` demo and GitHub links (the values are user-typed).

### 3.10 Shared components
All in `src/components/`, one folder each, default export. See every one of them, in every state, at **`/dev/components`** (dev builds only).

| Component | Use it for | Notes |
|---|---|---|
| `Button` | Every button | Variants `primary` · `secondary` · `ghost` · `danger` (delete/reject only). `isLoading` shows a spinner and blocks clicks but keeps the full colour (busy, not unavailable); `disabled` turns it grey. **`type` defaults to `"button"`**, so form submit buttons must say `type="submit"`. |
| `buttonClassName(variant, extra, size)` | A link that should look like a button | `<PrefetchLink className={buttonClassName("secondary")}>`. Both it and `Button` take `size`: `md` (44px, default) or `lg` (48px, Landing calls to action). |
| `Card` | The glass panel | `as="article" \| "section" \| "li"`, `padding="none" \| "md" \| "lg"`. |
| `Badge` | Status / category labels | Tones `mint` · `mustard` · `red` · `neutral`. Map values to tones next to their label map in `utils/`. |
| `Spinner`, `Skeleton` | Loading | Skeleton is sized with `className` (`"h-6 w-40"`); the pulse stops under reduced motion. |
| `EmptyState` | A list that loaded but is empty | `title`, optional `message` and `action`. |
| `ErrorState` | Data that failed to load | Pass the query's `refetch` as `onRetry`. |
| `Pagination` | Paginated lists | `page`, `totalPages` from the backend; hidden when there is one page. Under 360px only the arrows show. |
| `Modal` | Any dialog | Native `<dialog>`: focus trap, Esc, focus return and the backdrop come from the browser. `dismissible={false}` while a request runs. Page scroll is locked in CSS (`index.css`). |
| `ConfirmDialog` | "Are you sure?" before delete/reject | `isPending` spins the button and blocks closing. |
| `TextField`, `TextArea`, `Select` | Form fields | Built on `Field` (label + hint + error). `error` turns the border red and is read out by screen readers. Optional fields are labelled "(optional)" automatically. |
| `Avatar` | A person's photo or initial | `name`, `imageUrl`, `size` (px). Decorative: put the name next to it. |
| `AdminRoute` | Wrapping admin-only pages | Not signed in → `/login`; not an admin → their own start page. The backend enforces the real rule. |
| `ProjectCard` | A project in a list | The whole card links to the project; the parent sets its width (rail: fixed, Projects page: grid column). |
| `useToast().showToast(msg, tone?)` | Short feedback after an action | `"success"` (default) or `"error"`; fades after 5 s, max 3 at once. |

### 3.11 The signed-in layout (sidebar)
```
App.tsx
  <Route element={<AppLayout/>}>
     <Route path="/projects" … />                                   ← public
     <Route path="/projects/new" element={<ProtectedRoute>…} />     ← signed in only
     <Route path="/profile" element={<ProtectedRoute>…} />
  </Route>
AppLayout
  laptop (≥1024px): <aside> sidebar  (logo · collapse button · SidebarNav · UserMenu)
  below 1024px:     top bar with ☰  → the same sidebar in a <dialog> drawer
  <main id="main"> <Suspense> <Outlet/>   ← the page
```
- **Links** come from `layouts/sidebar/navItems.ts`, in groups ("General", later "Admin" with `adminOnly: true`). A link is added only when its page exists; `requiresAuth: true` hides it from visitors.
- **Visitors** can open the public pages (Projects) inside the same layout. The bottom of the sidebar then shows **Log in / Register** instead of the user menu (nothing at all while a stored session is still being restored, so signed-in people don't see a flash of "Log in").
- **Active link:** `NavLink` highlights the open page and sets `aria-current="page"`.
- **Collapse** (laptop only) shrinks the sidebar to icons and is remembered in `localStorage` (`sees.sidebar.collapsed`, inside try/catch). Collapsed labels stay readable by screen readers, and hovering shows a tooltip.
- **Phone drawer** uses `useModalDialog`, so focus trap, Esc, focus return and scroll lock work like `Modal`. It closes on a link, Esc, a tap outside, or when the window grows to laptop size. It slides in and out (and the backdrop fades); the slide-out relies on `transition-discrete`, so browsers without it just close instantly. Reduced-motion users get no animation.
- **User menu** uses the browser's `popover` attribute (closes on Esc or click-away, no JS of ours). It is pinned to the bottom-left, where the sidebar always is.
- **Skip link:** the first Tab on any signed-in page focuses "Skip to content", which jumps past the sidebar.
- **Loading:** `AppLayout` is its own chunk (~4 KB gz), so Landing never downloads it. Prefetching any page inside it also prefetches the layout (`LAYOUT_PAGES` in `pageLoaders.ts`). Links with an id (`/projects/abc`) are matched by `PAGE_FOR_PATTERN`.
- **Icons:** `lucide-react`. Import each icon by name; only the icons used end up in the bundle. Always pass `aria-hidden="true"` next to visible text.

### 3.12 Projects
| Route | Who | Page |
|---|---|---|
| `/projects` | anyone | `ProjectsList`: category/status filters, 12 per page |
| `/projects/:id` | anyone | `ProjectDetail`: Edit/Delete only when `canEditProject` |
| `/projects/new` | signed in | `NewProject` → `ProjectForm` |
| `/projects/:id/edit` | creator or admin | `EditProject` → `ProjectForm`; others see "You can't edit this project" |

- **Filters and page live in the address bar** (`?category=IOT&status=COMPLETED&page=2`) via `useUrlFilters` (§3.13). Back/Forward and shared links work, and no effect syncs them. Unknown values (typed by hand) count as "no filter" (`isProjectCategory` / `isProjectStatus`). Changing a filter returns to page 1.
- **While the next page loads** the old cards stay, dimmed (`keepPreviousData`), instead of flashing to skeletons.
- **Opening a project from a list is instant:** `useProject` uses the list's copy as placeholder data while the fresh record loads. `EditProject` waits for the fresh record, because the form copies its starting values once.
- **Permissions** come from `utils/canEditProject.ts`, which mirrors the backend rule (creator or admin). The UI only hides what can't be done; the backend still decides.
- **`ProjectForm`** owns the field values and validation (`projectFormValues.ts`: limits copied from the backend schema, per-field messages, and `toPayload` turning empty links into `null`). The pages decide what Save does. `noValidate` replaces the browser's popups with our own messages, and the first invalid field gets focus.
- **Tech stack** chips: Enter or comma adds one, Backspace on an empty box removes the last, and text left in the box is added when it loses focus. Max 20 chips of 50 characters (backend limits).
- **Members:** on create the creator is sent as the only member (`member_ids: [user.id]`). Edit never sends `member_ids`, so the backend keeps the team. A member picker needs a user-search endpoint the backend doesn't have yet.
- **No thumbnail field** until `/upload/image` exists. Cards and the detail page show the category as a stand-in.
- **After a change:** create/update put the new record straight into the detail cache and refresh every list. Delete removes the detail and refreshes the lists.

### 3.13 Hardware and loans
| Route | Who | Page |
|---|---|---|
| `/hardware` | anyone | `HardwareList`: category/availability filters, 12 per page; "Request loan" opens `LoanRequestModal` |
| `/loans` | signed in | `MyLoans`: "Current" (pending, on loan) and "History" (returned, rejected) |

- **Shared list filters:** `useUrlFilters()` gives `page`, `read(name, guard)` (a value only counts if the guard recognises it), `setFilter` (returns to page 1), `setPage` (scrolls to the top) and `clearAll`. Projects and Hardware both use it.
- **The card's action matches what the backend would allow:** your pending/approved loan → a link to My Loans. Under maintenance or none left → the reason, for everyone. Visitor → "Log in to borrow". Otherwise "Request loan". The backend refuses duplicates, maintenance items and empty shelves, so nobody fills in a request that's bound to fail.
- **Units only move on approval** (backend rule): a request doesn't change the shelf, so `useRequestLoan` just adds the returned loan to the My Loans cache. That updates the card at once. `useReturnLoan` refreshes My Loans and the hardware lists.
- **Focus after a request:** the card's button is replaced by a link, so the dialog can't return focus to it. `HardwareList` focuses the new link (`cardActionId`) two frames after closing. Cancelling still returns focus to the button the normal way.
- **Return date:** optional, can't be before tomorrow, sent as the end of that day in the borrower's time zone.
- **Loan names are a stopgap:** loans only carry `hardware_id`, so `useHardwareNames` fetches each distinct item once (cached for an hour). Remove it when the backend includes the name (DECISIONS open item 16).
- **Overdue:** an approved loan past its due date gets a red "Overdue" badge.
- **Not here:** adding, editing or retiring hardware and approving or rejecting loans are admin pages (Phase 3). There's no "cancel my request" endpoint.

## 4. Every `useEffect` and why it exists

The team rule is "justify every effect". There are exactly five, each with a comment in the code (API reads use `useQuery` instead of an effect, §3.4):

| Where | Why it must be an effect |
|---|---|
| `AuthProvider` | On mount: restore a session from browser storage, and subscribe to the API client's session-expired signal — both are external systems. |
| `usePrefetchAuthPages` | Wait for the browser's idle time — an external scheduler. |
| `useModalDialog` (Modal, phone drawer) | Sync the `open` prop to the `<dialog>` element's `showModal()` / `close()` — a DOM API with no attribute equivalent for a modal. |
| `AppLayout` | Listen for the window reaching laptop width and close the phone drawer — screen size is outside React. |
| `ImageGenerator` | Revoke the preview's object URL when it changes or on unmount — an external resource that must also be cleaned up on unmount. |

Everything else (form state, edit/view toggles, upload state) is plain state and event handlers.

## 5. Conventions we followed

- **Components small and single-purpose** (all under the ~150–200 line guideline; the largest is `Register` at ~147). `Profile` and `Landing` are shells that compose focused pieces.
- **Shared component = used on 2+ pages** (`TextField`, `PrefetchLink`, `ProtectedRoute`); otherwise it stays next to its page.
- **Use the shared components** (§3.10) instead of re-typing their classes: no hand-written button, card or input styles in pages.
- **Helpers live in their own `.ts` file** (`buttonClassName.ts`, `fieldStyles.ts`), not in a component file; React's fast refresh (and our lint rule) needs component files to export only components.
- **Named exports for pages**, default exports for shared components.
- **Responsive by default:** mobile-first Tailwind classes, breakpoints at `md` (768px); tap targets at least 44px (`min-h-11`); rail arrows tablet-and-up.
- **Images:** `loading="lazy"`, `decoding="async"`, explicit `width`/`height` (Profile's avatar isn't lazy — it's at the top of its page).
- **No blur on cards, no `background-attachment: fixed`** (measured to cost real frame time on phones).
- **Untrusted URLs** from the database are only linked if they start with `http://` or `https://`.
- **Text that users or the database supply must wrap.** Put `wrap-anywhere` on the element (names, emails, titles, descriptions, tags); otherwise a long unbroken word overflows the card or scrolls the whole page on a phone.
- **Storage:** session tokens go through `tokenStore` only. The projects cache (`useProjects`) uses `localStorage` directly but inside `try/catch`, because it is optional.
- **No mock data**, and no direct `axios` imports outside `src/api/`.

## 6. Adding a new page

1. Create `src/pages/<feature>/<Name>.tsx` with a **named export**.
2. Add a loader in `routes/pageLoaders.ts` (`name: () => import("../pages/<feature>/<Name>")`) and, if links should prefetch it, a path entry in `PAGE_FOR_PATH`.
3. In `App.tsx` add `const Name = lazy(() => pageLoaders.name().then((m) => ({ default: m.Name })))` and a `<Route>`. **Signed-in pages go inside the `AppLayout` route** (they get the sidebar and the login check); also add the page name to `SIGNED_IN_PAGES` in `pageLoaders.ts` and its link to `layouts/sidebar/navItems.ts`. Admin pages are additionally wrapped in `AdminRoute`.
4. Link to it with `PrefetchLink` (from `components/PrefetchLink`) instead of `Link`.
5. Read the user with `useAuth()`; never call the API from the component directly.
6. Check it at 320, 390 and 820 px, and that every tap target is at least 44px.

## 7. Adding an API call

1. Add or extend the type in `src/types/` (mirror the backend schema).
2. Add a function in `src/api/<thing>.ts`: `return unwrap<YourType>(api.get("/path"))`.
3. If a page needs it on load, wrap it in a `useQuery` hook under `src/hooks/` and add its key to `api/queryKeys.ts` (§3.4); otherwise call it from an event handler. After a change, invalidate the keys it affected.
4. Show `errorMessage(error, "fallback")` to the user, and design the failure state, not just the happy path.

## 8. Theme and styling

Tailwind v4 has no `tailwind.config.js`: the theme is the `@theme` block in `src/index.css`, and each token becomes utility classes automatically.

| Token | Value | Used as |
|---|---|---|
| `sees-void` | `#000f0d` | page base, input backgrounds (`bg-sees-void/60`) |
| `sees-forest` | `#002d22` | text on mint buttons |
| `sees-teal` | `#004d40` | borders (`border-sees-teal/40`) |
| `sees-mint` | `#a7ffeb` | headings, primary buttons, accents |
| `sees-mustard` | `#e4a11b` | links, secondary accent |
| `sees-glass` | `rgba(0,45,34,.4)` | placeholder panels |
| gradients | `gradient-sees`, `gradient-card` | page background layer, card backgrounds (`bg-gradient-card`) |
| shadows | `sees-glow`, `sees-card`, `sees-active` | `shadow-sees-card` etc. |
| fonts | `Inter Variable` (sans), `JetBrains Mono` (mono, small labels) | self-hosted through `@fontsource` |

The page gradient is drawn by `body::before` on its own fixed layer (not `background-attachment: fixed`). `--blur-sees`, the `sees-active` shadow and the marquee / wave-pulse animations are defined in the theme (carried over from v1, where the marquee belonged to the scroll-driven hero that is the candidate for Phase 6) but **currently unused** (checked by searching the components). The official tokens are Ifeoluwa's task; ours match the docs' three brand colours and the rest come from v1.

## 9. What is not in this repository

There is **no automated test suite** yet. Everything in this codebase was checked with throwaway scripts (a simulated browser against the live backend, headless Edge driven over the DevTools protocol, and Lighthouse) kept outside the repo, and none of their tooling is in `package.json`. To repeat them, install the tools in a temporary folder, run the backend from `backend/`, and serve `dist/` with compression and long-lived caching so the numbers are realistic. Adding Vitest (component and hook tests) and Playwright (browser flows) would turn these one-off checks into permanent ones.

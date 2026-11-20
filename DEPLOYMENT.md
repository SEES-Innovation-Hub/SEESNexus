# Deploying SEES Nexus

```
Browser ──► Vercel  (frontend: static React build, global CDN)
   │
   └──► Heroku  (backend: FastAPI in Docker, region eu) ──► Heroku Postgres
                     ├──► Cloudinary (images)
                     └──► Brevo (email)
```

- **Backend:** Heroku, container stack. `heroku.yml` builds `backend/Dockerfile`, and its release
  phase runs `alembic upgrade head` before each version goes live. If a migration fails, the release
  stops and the previous version keeps serving.
- **Frontend:** Vercel, from the `frontend/` folder. `frontend/vercel.json` sends every path to
  `index.html` (so links like `/events/123` load on refresh) and sets security and caching headers.

Plan names, prices and limits below were right when this was written; check Heroku's pricing page
before choosing.

> **Use fresh secrets.** Old keys may have leaked in the November 2026 compromise of the old `master`
> branch. Generate new values for everything below; don't copy anything from an old `.env`.

---

## 1. Backend on Heroku

Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) and run `heroku login`.
Replace `sees-nexus-api` with your app name throughout.

### 1.1 Create the app and database

```bash
heroku create sees-nexus-api --region eu --stack container
heroku addons:create heroku-postgresql:essential-0 -a sees-nexus-api
```

- `--region eu`: Heroku's Common Runtime only offers the US and Europe, and Europe is closer to Lagos.
- `--stack container`: tells Heroku to build from `heroku.yml`.
- The Postgres add-on sets `DATABASE_URL` for you. The app accepts its `postgres://` form as is.

### 1.2 Settings

Generate the two secrets first:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"   # SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"   # ADMIN_REGISTRATION_KEY
```

Then set them, with everything else:

```bash
heroku config:set -a sees-nexus-api \
  SECRET_KEY='<generated>' \
  ADMIN_REGISTRATION_KEY='<generated>' \
  DATABASE_SSL=require \
  TRUSTED_PROXY_COUNT=1 \
  WEB_CONCURRENCY=2 DB_POOL_SIZE=4 DB_MAX_OVERFLOW=4 \
  OTP_DEBUG_RETURN_CODE=false \
  BREVO_API_KEY='<from Brevo>' BREVO_SENDER_EMAIL='<verified sender>' BREVO_SENDER_NAME='SEES Nexus' \
  CLOUDINARY_CLOUD_NAME='<…>' CLOUDINARY_API_KEY='<…>' CLOUDINARY_API_SECRET='<…>' \
  CORS_ORIGINS='https://placeholder.invalid'
```

`CORS_ORIGINS` gets its real value in step 3, once Vercel has given you the frontend's address.

| Setting | Why |
|---|---|
| `SECRET_KEY` | Signs every login token. The app refuses to start against Postgres with the default or the `.env.example` placeholder. |
| `ADMIN_REGISTRATION_KEY` | The only way anyone becomes an admin (at sign-up, or when an admin promotes someone). At least 24 characters. Share it privately. |
| `DATABASE_SSL=require` | Heroku Postgres refuses unencrypted connections. |
| `TRUSTED_PROXY_COUNT=1` | Rate limits are per visitor IP. Without it every visitor looks like Heroku's router and they all share one limit. |
| `WEB_CONCURRENCY`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | 2 workers × (4 + 4) = at most 16 database connections, under essential-0's limit of 20, with room for the release phase and `heroku pg:psql`. |
| `OTP_DEBUG_RETURN_CODE=false` | Belt and braces: the code is never returned once Brevo is configured anyway. |
| `BREVO_*` | Sign-up codes, password resets, waitlist emails. Verify the sender (better: the whole domain, with SPF and DKIM) in Brevo, or emails land in spam. |
| `CLOUDINARY_*` | Image uploads. Without them the forms offer "paste a link" instead. |
| `CORS_ORIGINS` | The frontend's address; the API refuses browser calls from anywhere else. |

### 1.3 Deploy from GitHub

In the Heroku dashboard, open the app, then **Deploy**, then **GitHub**:

1. Connect `SEES-Innovation-Hub/SEESNexus`.
2. Under **Automatic deploys**, choose the `main` branch, tick **Wait for CI to pass before deploy**,
   and enable it.
3. Under **Manual deploy**, deploy `main` once now.

Watch it:

```bash
heroku releases -a sees-nexus-api            # the release phase (migrations) shows here
heroku logs --tail -a sees-nexus-api
```

### 1.4 Dyno size

```bash
heroku ps:type web=basic -a sees-nexus-api
```

Basic doesn't sleep. Eco is cheaper but sleeps after 30 minutes idle, and the next visitor waits
while it wakes.

### 1.5 Check it

```bash
heroku info -a sees-nexus-api                 # note the "Web URL"
curl https://<web-url>/health                 # {"status":"success",...}; 503 if the database is unreachable
```

`/docs` on the same address shows the API.

### 1.6 Backups

```bash
heroku pg:backups:schedule DATABASE_URL --at '02:00 Africa/Lagos' -a sees-nexus-api
heroku pg:backups:capture -a sees-nexus-api   # one now, to be sure it works
```

---

## 2. Frontend on Vercel

1. In Vercel, **Add New → Project**, then import `SEES-Innovation-Hub/SEESNexus`.
2. **Root Directory:** `frontend`. Vercel detects Vite: build `npm run build`, output `dist`.
3. **Environment variable:** `VITE_API_URL` = the Heroku web URL from step 1.5, with no trailing
   slash, e.g. `https://sees-nexus-api-xxxxxxxx.herokuapp.com`. It is read when the frontend is built,
   so redeploy after changing it.
4. **Production branch:** `main` (Settings → Git).
5. Deploy, and note the address Vercel gives you (and your custom domain, if you add one).

---

## 3. Connect the two

Allow the frontend's address(es) to call the API, comma-separated, with no trailing slash:

```bash
heroku config:set CORS_ORIGINS='https://sees-nexus.vercel.app' -a sees-nexus-api
```

Heroku restarts the app with the new setting. Vercel preview deployments have their own addresses and
won't be able to call the production API unless you add them too.

---

## 4. First admin and smoke test

The seed script is for local development only: never run it in production.

1. Open the Vercel site and register with **I'm registering as an admin** ticked and the admin key.
   You'll get the email code from Brevo.
2. Check, in this order:
   - Admin overview loads with real counts.
   - Create an event, then register for it from a second (student) account.
   - Upload a project thumbnail (Cloudinary).
   - "Forgot your password?" sends an email and the reset works.
   - Ten wrong passwords on one account give "Too many attempts".
3. Point an uptime monitor (UptimeRobot or similar) at `https://<web-url>/health`.

---

## Day to day

- **Deploying:** merge to `main`. CI runs; Heroku and Vercel deploy when it's green.
- **Rolling back the backend:** `heroku releases:rollback -a sees-nexus-api`. This does not undo
  database migrations. If a release changed the schema, restore a backup or ship a fix instead.
- **Rolling back the frontend:** Vercel → Deployments → promote an earlier one.
- **Changing a setting:** `heroku config:set …` restarts the app. Changing `VITE_API_URL` on Vercel
  needs a redeploy.
- **Database shell:** `heroku pg:psql -a sees-nexus-api`.

## Rough monthly cost

| Item | Plan | ≈ USD |
|---|---|---|
| Heroku web dyno | Basic | 7 |
| Heroku Postgres | essential-0 | 5 |
| Vercel | Hobby | 0 |
| Cloudinary, Brevo | free tiers | 0 |
| **Total** | | **≈ 12** |

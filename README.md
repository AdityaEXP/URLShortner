# URL Shortener

A URL shortener with a Flask API and a small React dashboard on top. Built against the Track B spec: shorten/redirect/stats/delete, plus the collision handling, expiry, rate limiting and auth pieces the assignment specifically asks for.

## Stack

- Backend: Flask, Postgres (psycopg2), Redis, JWT + API key auth
- Frontend: React + Vite, Tailwind
- Rate limiting, short code generation and click counting are all hand-rolled — no flask-limiter, no shortuuid, per the assignment constraints

## Running it locally

You need Postgres and Redis reachable somewhere (both default to `localhost` in the example env files).

### Backend

```
cd backend
python -m venv venv
venv\Scripts\activate       
pip install -r requirements.txt
copy .env.example .env       # fill in DB_URL, SECRET_KEY, REDIS_URL
python run.py
```

Runs on `http://localhost:5000`.

### Frontend

```
cd frontend
npm install
copy .env.example .env       # change VITE_API_BASE_URL if the backend isn't on localhost:5000
npm run dev
```

Runs on `http://localhost:5173`.

## Backend environment variables

| Variable | Purpose |
|---|---|
| `DB_URL` | Postgres connection string |
| `SECRET_KEY` | signs the JWTs |
| `ALGORITHM` | JWT algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry |
| `BASE_URL` | used to build the full `short_url` in responses |
| `REDIS_URL` | Redis connection string |
| `SHORTEN_RATE_LIMIT_PER_MINUTE` | shorten requests allowed per IP per minute |
| `TAKE_N` | length of generated short codes |
| `LINK_CACHE_TTL_SECONDS` | how long a redirect stays cached in Redis |
| `NEGATIVE_CACHE_TTL_SECONDS` | how long a "not found" result stays cached |
| `CLICK_FLUSH_INTERVAL_SECONDS` | how often pending click counts get written to Postgres |

## API

### POST /auth/signup
```json
{ "username": "aditya", "email": "aditya@example.com", "password": "password123" }
```
→ 201
```json
{ "access_token": "...", "token_type": "bearer" }
```

### POST /auth/login
Same response shape as signup. Body is `{ "email": "...", "password": "..." }`.

### POST /auth/api-key
Header: `Authorization: Bearer <token>`

→ 201 `{ "api_key": "sk_..." }`

Only shown once. Calling this again rotates the key — the old one stops working immediately.

### POST /shorten
Header: `Authorization: Bearer <token>`
```json
{ "url": "https://example.com/some/long/path", "alias": "myco", "expires_in_minutes": 60 }
```
`alias` and `expires_in_minutes` are optional.

→ 201
```json
{ "short_code": "myco", "short_url": "http://localhost:5000/myco", "created_at": "2026-09-18T16:54:14+05:30" }
```

Rate limited to `SHORTEN_RATE_LIMIT_PER_MINUTE` requests per IP per minute — a 429 comes back past that.

### GET /\<code\>
302 redirect to the original URL. 404 if the code doesn't exist, 410 if it's expired.

### GET /stats/\<code\>
→ 200
```json
{ "original_url": "https://example.com/some/long/path", "click_count": 12, "created_at": "2026-09-18T16:54:14+05:30" }
```

### DELETE /\<code\>
Needs either `Authorization: Bearer <token>` or `X-API-Key: <key>`, and you have to own the link. 204 on success, 403 if it's not yours, 404 if it doesn't exist.

### GET /analytics
Top 5 most-clicked links, no auth needed.
```json
[{ "short_code": "myco", "click_count": 12 }, { "short_code": "abc123", "click_count": 4 }]
```

## Design decisions

### Collision handling
Short codes are `sha256(url + id)`, re-encoded in base62, truncated to 7 characters. The `id` comes from the Postgres sequence, reserved with `nextval()` *before* the row is inserted — so if there's a collision, retrying just means grabbing a fresh id and hashing again, no extra salt needed, since sequence values are never reused even after a rollback.

Went with hashing the id instead of just base62-encoding it directly, even though `base62(id)` alone would never collide. The reason: `base62(id)` is sequential and guessable — id 1, 2, 3... means anyone can enumerate every link ever created just by walking the numbers. Hashing first breaks that at the cost of needing the retry logic.

Also switched from plain hex to base62 partway through — hex only gives `16^7` (~268M) possible codes, base62 gives `62^7` (~3.5 trillion), which matters a lot once you think about collision odds at real scale.

Decided to move flush click outside of the api as seperate worker, cause if there are multiple instance it will be safe but there will be duplicated work.

### Auth: JWT and API key, not just one
DELETE accepts either a JWT or an API key. JWT covers the case where the frontend already has you logged in and shouldn't need a separate key just to delete something you made. The API key exists because the assignment specifically wants delete protected by "an API key header" for script/programmatic use. It's stored hashed with sha256, not bcrypt — the key is already high-entropy since we generate it (nothing to brute-force), and bcrypt's random salt would make it impossible to look up by exact match on every request anyway.

### Caching
`GET /<code>` checks Redis before touching Postgres. Cache TTL is capped by the link's own expiry so an expiring link never gets served stale past when it should actually be gone. Unknown codes get cached too (as a "not found" marker, 30s) so random/bot traffic hitting bogus codes doesn't fall through to Postgres on every single request.

### Click counting
Every redirect does a Redis `INCR`, not a Postgres write — a link going viral shouldn't turn into a write-lock bottleneck on one row. A background job (APScheduler) flushes pending counts into Postgres every few seconds. `/stats` always merges the Postgres count with whatever's still pending in Redis, so it's accurate even between flushes. Tradeoff: a few seconds of clicks could be lost if Redis dies right before a flush — acceptable for analytics, would not be acceptable for anything that needs to be exact.

### Rate limiting
Redis `INCR` + `EXPIRE`, fixed window, keyed by IP and endpoint. The TTL is set with `SET key 0 EX 60 NX` *before* the `INCR`, specifically so the key is guaranteed to have a TTL from the moment it's created — otherwise a crash between `INCR` and a separate `EXPIRE` call could leave a key that counts forever with no expiry, permanently rate-limiting that IP.

### Redirect is 302, not 301
A 301 gets cached by the browser permanently, meaning repeat visits from the same browser would never hit the server again — breaking both click counting and expiry checks after the first visit, not just "undercounting" clicks.

## What's not done
- No automated tests. Everything here was verified by hand against a live server while building it.
- No SSRF protection — a valid `http://localhost/...` or internal-IP URL would still be accepted and redirected to.
- Single backend process assumed. The rate limiter and click flush both use atomic Redis ops so they're safe under multiple instances, but nothing's been tested at that scale.

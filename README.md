# URL Shortener

A URL shortener with a Flask API and a small React dashboard on top. Built against the Track B spec: shorten/redirect/stats/delete, plus the collision handling, expiry, rate limiting and auth pieces the assignment specifically asks for.

## Stack

- Backend: Flask, Postgres (psycopg2), Redis, JWT + API key auth
- Frontend: React + Vite, Tailwind
- Rate limiting, short code generation and click counting are all hand-rolled — no flask-limiter, no shortuuid, per the assignment constraints

## Deployed

- Frontend: https://url-shortner-bay-phi.vercel.app
- Backend: https://urlshortner-2u1f.onrender.com

Backend runs on Render's free tier, which spins down after 15 minutes with no traffic. First request after that can take 40-50 seconds to come back — that's Render waking the instance up, not a bug.

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

### Custom aliases
Aliases go through the same character/length validation as everything else (`[a-zA-Z0-9_-]`, 3-20 chars), plus one more check: a small blocklist of words that collide with real routes (`shorten`, `stats`, `analytics`, `auth`, `static`). Flask always matches a static route like `/analytics` before it tries the dynamic `/<code>` redirect route, so if someone claimed `analytics` as an alias, that link would be permanently unreachable — every request to it would hit the analytics endpoint instead of the redirect. Precomputing that blocklist once was simpler than trying to detect the clash generically at request time.

### Auth: JWT and API key, not just one
DELETE accepts either a JWT or an API key, on purpose, so both kinds of caller are covered. JWT lets a logged-in user delete a link straight from the dashboard without needing to separately generate and paste in an API key first. The API key exists because the assignment specifically wants delete protected by "an API key header" for script/programmatic use. It's stored hashed with sha256, not bcrypt — the key is already high-entropy since it's generated, not user-chosen, so there's nothing to brute-force, and bcrypt's random salt would make it impossible to look up by exact match on every request anyway.

### Input validation
`url` is typed as pydantic's `HttpUrl`, which only accepts `http`/`https` schemes — that alone is what rejects something like `javascript:alert(1)`, no custom regex needed.

### Caching
`GET /<code>` checks Redis before ever touching Postgres. On a miss, it reads Postgres once and writes the URL into Redis with `TTL = min(default TTL, time left until the link expires)`, so a link never gets served from cache past the point it should actually be gone — and every redirect after the first one for that code skips the database entirely.

Unknown codes get cached too, as a short-lived "not found" marker (30s). Without that, a normal cache only helps for codes that exist — someone spamming random or guessed codes would still hit Postgres on every single request.

There's one sharp edge with the negative cache: if a code gets requested the instant before it's created (someone probing an alias right as another user is about to claim it), that 404 gets cached. So the cache is explicitly cleared again right after a link is created, closing that window. Same idea on delete — the cache entry is invalidated immediately so a deleted link can't keep redirecting off a stale cache hit.

### Click counting
Every redirect does a Redis `INCR`, not a Postgres write — a link going viral shouldn't turn into a write-lock bottleneck on one row. A background worker (APScheduler, running inside the process, not triggered per-request) flushes pending counts into Postgres every few seconds. `/stats` always merges the Postgres count with whatever's still pending in Redis, so it reads correctly even between flushes.

Running the flush as its own worker instead of tying it to a request keeps it on a fixed schedule regardless of traffic. The tradeoff shows up if this ever runs as more than one instance: each instance would run its own flush loop and re-scan the same Redis keys. That's still *safe* — Redis's `GETDEL` is atomic, so nothing gets double-counted — just wasteful, duplicated work across instances for no extra benefit. Fine for a single instance, worth knowing if this ever needs to scale out.

Also worth stating plainly: a few seconds of clicks can be lost if Redis dies right before a flush. Acceptable for analytics, would not be acceptable for anything that needs to be exact.

### Rate limiting
Redis `INCR` + `EXPIRE`, fixed window, keyed by IP and endpoint. Redis instead of a plain Python dict specifically because the limit has to hold even if this ever runs as more than one process — a dict's counters live inside one process's memory, so two instances would each independently allow the full limit, effectively doubling it.

The TTL is set with `SET key 0 EX 60 NX` *before* the `INCR`, so the key is guaranteed to have a TTL from the moment it's created — otherwise a crash between `INCR` and a separate `EXPIRE` call could leave a key that counts forever with no expiry, permanently rate-limiting that IP.

Known limitation: a fixed window allows a burst of up to 2x the limit right at the boundary between two windows — 10 requests in the last second of one minute, 10 more in the first second of the next, both technically "within limit." A sliding window algorithm fixes that, but it means storing a timestamp per request instead of a single counter, which is both more code to implement and noticeably less memory-efficient at any real scale. Chose the simple version and accepted the boundary case as a known limitation rather than the added complexity.

### Analytics
`GET /analytics` is a plain `SELECT short_code, click_count FROM links ORDER BY click_count DESC LIMIT 5`, backed by an index on `click_count`. It's global across all users, not scoped per account — anyone can see the site-wide top 5. Numbers are stale by at most `CLICK_FLUSH_INTERVAL_SECONDS` (5s), since that's how long a click can sit in Redis before it lands in Postgres.

This started out as a Redis sorted set (`ZINCRBY` per click, `ZREVRANGE` to read the top 5) — the textbook `O(log n)` way to do a leaderboard. Dropped it because invalidating it correctly turned out to be the hard part, not the read speed: a deleted link has to be `ZREM`'d separately from its row being deleted, and if Redis ever restarted, the sorted set would come back empty while Postgres still had the real totals — two sources of truth that could silently disagree. Querying Postgres directly removes that whole class of bug, and an indexed `ORDER BY ... LIMIT 5` is cheap enough that the theoretical `O(log n)` win from Redis wasn't worth the consistency risk.

### Redirect is 302, not 301
A 301 gets cached by the browser permanently, meaning repeat visits from the same browser would never hit the server again — breaking both click counting and expiry checks after the first visit, not just "undercounting" clicks.

### Indexes
- `links.short_code` (UNIQUE): O(log n) redirect lookup on cache miss. Also the collision detector: a duplicate insert raises UniqueViolation, which triggers a retry for generated codes or a 409 for custom aliases. No check-then-insert race.
- `links.click_count`: powers `/analytics` (top 5 active links). Tradeoff: every click-count update also touches this index, which is part of why counts are flushed in 5-second batches instead of written per click.
- `links.owner_id`: without it, per-user queries and cascading user deletes would scan the whole table.
- `users.api_key_hash` (UNIQUE): keys are hashed with sha256, not bcrypt, so the hash is deterministic and indexable. Safe because keys are 32 random bytes — passwords, which are low-entropy, still use bcrypt.
- Not indexed on purpose: `expires_at` (checked on an already-fetched row), `original_url` (URLs aren't deduplicated — each shorten creates a new code).

## What's not done
- No automated tests. Everything here was verified by hand against a live server while building it.
- No phishing/malware blocklist — a malicious URL can hide behind a short link just as easily as a legitimate one.
- Single backend process assumed for now. The rate limiter and click flush both use atomic Redis ops so running multiple instances would still be *correct*, just with some duplicated work (see Click counting above).

# URL Shortener

A simple URL shortener with a Flask API and a small React dashboard

It follows the Track B spec and supports shortening links redirects stats delete expiry rate limiting auth and collision handling

## Stack

- Backend -- Flask Postgres with psycopg2 Redis JWT and API key auth
- Frontend -- React Vite and Tailwind
- Rate limiting short code generation and click counting are built by hand as required by the assignment

## Deployed

- Frontend -- https://url-shortner-bay-phi.vercel.app
- Backend -- https://urlshortner-2u1f.onrender.com

The backend is running on Render free tier

Render shuts the server down after 15 minutes without traffic so the first request can take around 40 to 50 seconds while the server starts again

## Running it locally

You need Postgres and Redis running somewhere

The example env files use localhost by default

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Add DB_URL SECRET_KEY and REDIS_URL to the env file

The backend runs on http://localhost:5000

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

If the backend is not running on localhost:5000 then change VITE_API_BASE_URL

The frontend runs on http://localhost:5173

## Backend environment variables

| Variable | Purpose |
|---|---|
| `DB_URL` | Postgres connection string |
| `SECRET_KEY` | Used to sign JWTs |
| `ALGORITHM` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry time |
| `BASE_URL` | Used to build the short URL |
| `REDIS_URL` | Redis connection string |
| `SHORTEN_RATE_LIMIT_PER_MINUTE` | Number of shorten requests allowed from one IP per minute |
| `TAKE_N` | Length of generated short codes |
| `LINK_CACHE_TTL_SECONDS` | How long redirects stay in Redis |
| `NEGATIVE_CACHE_TTL_SECONDS` | How long missing codes stay cached |
| `CLICK_FLUSH_INTERVAL_SECONDS` | How often click counts are saved to Postgres |

## API

### POST /auth/signup

```json
{
  "username": "aditya",
  "email": "aditya@example.com",
  "password": "password123"
}
```

Returns 201

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

### POST /auth/login

Uses the same response as signup

Body

```json
{
  "email": "...",
  "password": "..."
}
```

### POST /auth/api-key

Send the JWT in the Authorization header

```text
Authorization: Bearer <token>
```

Returns 201

```json
{
  "api_key": "sk_..."
}
```

The key is only shown once

Calling this endpoint again creates a new key and the old one stops working

### POST /shorten

Send the JWT in the Authorization header

```text
Authorization: Bearer <token>
```

Example body

```json
{
  "url": "https://example.com/some/long/path",
  "alias": "myco",
  "expires_in_minutes": 60
}
```

Alias and expiry are optional

Returns 201

```json
{
  "short_code": "myco",
  "short_url": "http://localhost:5000/myco",
  "created_at": "2026-09-18T16:54:14+05:30"
}
```

The endpoint is rate limited by IP

A 429 response is returned after the limit is reached

### GET /<code>

Returns a 302 redirect to the original URL

Returns 404 when the code does not exist

Returns 410 when the link has expired

### GET /stats/<code>

Returns the original URL click count and creation time

Example

```json
{
  "original_url": "https://example.com/some/long/path",
  "click_count": 12,
  "created_at": "2026-09-18T16:54:14+05:30"
}
```

### DELETE /<code>

Needs either a JWT or an API key

The user also has to own the link

Returns 204 on success

Returns 403 when the link belongs to someone else

Returns 404 when the link does not exist

### GET /analytics

Shows the top 5 most clicked links

No auth is needed

```json
[
  {
    "short_code": "myco",
    "click_count": 12
  },
  {
    "short_code": "abc123",
    "click_count": 4
  }
]
```

## Design decisions

### Collision handling

Short codes are made from sha256 of the URL and a Postgres id

The hash is converted to base62 and then cut down to 7 characters

The Postgres id is reserved before the row is inserted

If a collision happens the code gets another id and tries again

Postgres sequences do not reuse ids after a rollback so there is no need for extra random salt

I used the id inside the hash instead of just using base62 on the id

Using base62 directly would make codes easy to guess

For example if one link has id 100 then the next links would have nearby codes

That would make it possible to keep guessing links

Hashing the id makes the codes much harder to guess

I also changed from hex to base62 during development

Seven hex characters gives about 268 million possible codes

Seven base62 characters gives about 3.5 trillion possible codes

That gives much more room before collisions become common

### Custom aliases

Aliases use the same validation as generated codes

They can contain letters numbers underscores and hyphens

They must be between 3 and 20 characters

Some names are blocked because they are already used by real routes

Examples are

```text
shorten
stats
analytics
auth
static
```

This is needed because Flask checks fixed routes before the dynamic redirect route

If someone used analytics as an alias then /analytics would always go to the analytics endpoint instead of the shortened link

Keeping a small blocklist was simpler than trying to detect route conflicts every time

### Auth

The delete endpoint accepts both JWT and API key auth

JWT is useful for the dashboard because a logged in user can delete a link without making an API key first

The API key is useful for scripts and programmatic requests

The assignment also specifically asks for an API key header

API keys are stored as sha256 hashes

The keys are generated from random bytes so they already have high entropy

That makes sha256 suitable here

Passwords are different because users choose them and they can have low entropy so passwords use bcrypt

### Input validation

The URL field uses pydantic HttpUrl

It only accepts http and https URLs

This also rejects things such as javascript URLs without needing a custom regex

### Caching

GET /<code> checks Redis before checking Postgres

If the link is already cached then Postgres is not touched

When the link is not cached the app reads it from Postgres and stores it in Redis

The cache TTL is the smaller of the normal cache TTL and the time left before the link expires

This stops an expired link from staying alive in Redis

Unknown codes are also cached for a short time

This is called negative caching

Without it random codes would keep reaching Postgres even when they do not exist

There is one small problem with negative caching

A user could request a code just before another user creates that same code

The first request would cache a 404

To handle this the cache is cleared after a link is created

The same thing happens when a link is deleted

The cache is cleared right away so an old cached redirect is not used

### Click counting

Every redirect increases a Redis counter instead of writing to Postgres

This avoids making a database write for every click

A background worker flushes the pending click counts into Postgres every few seconds

The stats endpoint also adds the pending Redis count to the saved Postgres count

This means the stats can still be correct before the next flush

The flush worker runs on a fixed schedule instead of waiting for a request

There is one limitation if the app is later run on multiple instances

Each instance would run its own flush worker

That means they could scan the same Redis keys more than once

It is still safe because Redis GETDEL is atomic so the same clicks cannot be counted twice

It would just do some duplicate work

For now the app assumes one backend instance

Another limitation is that a few seconds of clicks could be lost if Redis goes down before a flush

That is acceptable for analytics but would not be okay for data that must be exact

### Rate limiting

Rate limiting uses Redis INCR and EXPIRE with a fixed time window

The key uses the IP and endpoint

Redis is used instead of a Python dictionary because the limit should still work when more than one backend process is running

A Python dictionary only exists inside one process

So two workers could each allow the full limit

Redis gives them one shared counter

The TTL is set when the key is first created

This avoids a small problem where the process could crash after INCR but before EXPIRE

Without the TTL the counter could stay forever

The fixed window method has a known edge case

A user could send the full limit at the end of one minute and the full limit again at the start of the next minute

So they could briefly send about twice the normal limit

A sliding window can reduce this issue

I did not use it because it needs to store request timestamps instead of one counter

That means more code and more memory use

For this project the simpler fixed window was enough and the boundary case is a known limitation

### Analytics

GET /analytics uses a simple Postgres query

```sql
SELECT short_code, click_count
FROM links
ORDER BY click_count DESC
LIMIT 5
```

There is an index on click_count

The list is global so it shows the top 5 links across all users

The numbers can be behind by up to the click flush interval

The current interval is 5 seconds

I first considered using a Redis sorted set

Each click would use ZINCRBY and the top links could be read with ZREVRANGE

That would be a good fit for a leaderboard

I dropped it because keeping the Redis data in sync was more complicated

For example deleting a link would also need a ZREM

A Redis restart could also remove the sorted set while Postgres still had the real totals

That would give two sources of truth

Using Postgres directly keeps one source of truth and the indexed query is cheap enough for this use case

### Redirect is 302

The redirect uses 302 instead of 301

A 301 can be cached by the browser for a long time

That means later visits might never reach the server

That would break click counting and could also bypass expiry checks

### Indexes

- `links.short_code` is unique and indexed so redirects can find a link quickly after a Redis miss
- The unique constraint also handles collisions without a separate check before insert
- `links.click_count` is used for the analytics query
- `links.owner_id` helps with user specific queries and deleting a users links
- `users.api_key_hash` is unique and indexed so API keys can be looked up by their sha256 hash
- `expires_at` is not indexed because it is checked after the link is already found
- `original_url` is not indexed because different links can point to the same URL

## What's not done

- No automated tests yet
- The project was tested by hand against the live server while building it
- There is no phishing or malware blocklist
- A malicious URL could still be hidden behind a short link
- The backend currently assumes one main process
- Multiple instances would still be correct because the Redis operations are atomic but the click flush workers could do some duplicate work

# Rent & Flatmate Finder

Flask + SQLite + Socket.IO app matching tenants to room listings using an
LLM-based (with rule-based fallback) compatibility score, with real-time
chat and email notifications.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in values (all optional except SECRET_KEY)
python app.py                 # runs on http://localhost:5000
```

Admin login is auto-seeded: `admin@rentflat.com` / `admin123`

## Deployment (Render / Railway)

1. Push this repo to GitHub.
2. Create a new Web Service, set build command `pip install -r requirements.txt`
   and start command from `Procfile` (`gunicorn --worker-class eventlet -w 1 app:app`).
3. Add environment variables from `.env.example`.
4. For persistent storage in production use Postgres: set `DATABASE_URL` to
   `postgresql://...` (SQLAlchemy handles it automatically) and add
   `psycopg2-binary` to requirements.

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| SECRET_KEY | yes | Flask session signing |
| DATABASE_URL | no | defaults to local SQLite |
| ANTHROPIC_API_KEY | no | enables real LLM scoring; falls back to rule-based if unset/fails |
| SMTP_HOST/PORT/USER/PASS | no | enables real email; falls back to console logging if unset |

## Database Schema

- **User**(id, name, email, password_hash, role[tenant/owner/admin])
- **Listing**(id, owner_id→User, location, rent, available_from, room_type, furnishing, photo_url, filled, created_at)
- **TenantProfile**(id, tenant_id→User, preferred_location, budget_min, budget_max, move_in_date)
- **Match**(id, tenant_id→User, listing_id→Listing, score, explanation, status[none/pending/accepted/declined], created_at) — one row per tenant-listing pair; score/explanation computed **once** and cached here, not recomputed on every request.
- **Message**(id, match_id→Match, sender_id→User, content, created_at) — chat persisted per match.

## LLM Compatibility Prompt

```
Given this room listing: location=<loc>, rent=<rent>, room_type=<type>, furnishing=<status>, available_from=<date>
and this tenant profile: preferred_location=<loc>, budget_min=<min>, budget_max=<max>, move_in_date=<date>

Compute a compatibility score from 0 to 100 based on budget and location match.
Return ONLY JSON: {"score": number, "explanation": string}
```

**Example input:** listing location="Koramangala", rent=15000; tenant preferred_location="Koramangala", budget 12000-18000
**Example output:** `{"score": 92, "explanation": "Rent fits comfortably within budget and location is an exact match."}`

If the LLM call fails or `ANTHROPIC_API_KEY` is unset, `compatibility.py` falls
back to a deterministic rule: 60 pts for rent inside budget range (partial
credit if outside, scaled by distance/budget span), 40 pts for
substring-match on location.

## API / Route Summary

| Route | Method | Role | Description |
|---|---|---|---|
| /register, /login, /logout | GET/POST | all | auth |
| / | GET | all | role-based dashboard |
| /listing/new | GET/POST | owner | create listing |
| /listing/<id>/fill | GET | owner | mark filled (hides from browse) |
| /profile | GET/POST | tenant | create/edit preferences |
| /browse?location= | GET | tenant | ranked listings by compatibility score |
| /interest/<listing_id> | GET | tenant | express interest, triggers owner email |
| /requests | GET | owner | pending interest requests |
| /respond/<match_id>/<accept\|decline> | GET | owner | respond, triggers tenant email |
| /chats | GET | both | list active (accepted) chats |
| /chat/<match_id> | GET | both | chat room UI |
| Socket.IO `join`, `send_message` / `receive_message` | ws | both | real-time chat, persisted to Message table |
| /admin/user/<id>/delete | GET | admin | user management |

## Notification Flow

1. Tenant clicks "Express Interest" → Match.status = pending → email to owner (flagged as high-priority copy if score > 80).
2. Owner accepts/declines from `/requests` → email to tenant with outcome.
3. On accept, both parties gain access to `/chat/<match_id>`, a Socket.IO room keyed by match id; messages persist to `Message` and replay on reload.

## Chat Implementation

Flask-SocketIO room per `match_id`. Client joins room on page load, emits
`send_message`; server persists to DB then broadcasts `receive_message` to
the room. Message history is loaded server-side on initial page render.

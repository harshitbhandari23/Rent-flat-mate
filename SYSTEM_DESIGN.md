# System Design Write-up (Rent & Flatmate Finder)

## Compatibility Scoring Design
Each tenant–listing pair is represented by a `Match` row keyed on
`(tenant_id, listing_id)`. When a tenant browses listings, the app checks
for an existing `Match`; if absent, it computes one via `get_compatibility_score()`
and persists the score, explanation, and a default `status='none'`. This
guarantees the score is computed exactly once per pair and simply read on
subsequent visits, satisfying "not recomputed on every request" while
keeping listings freshly ranked (sorted descending by cached score at
render time). If a listing or profile changes materially, a future
enhancement would invalidate and recompute the affected Match rows.

## LLM Integration and Fallback
`compatibility.py` isolates all scoring logic behind one function,
`get_compatibility_score(profile, listing)`. When `ANTHROPIC_API_KEY` is
configured, it sends a compact prompt describing both entities and asks
Claude to return strict JSON (`{score, explanation}`), which is parsed
after stripping markdown fences. Any failure — missing key, network error,
malformed JSON, timeout — is caught and silently degrades to
`rule_based_score()`, a deterministic function giving up to 60 points for
budget fit (full credit inside range, linearly decayed by distance outside
it) and 40 points for a location substring match. This two-tier design
means the product never breaks due to LLM outages and the fallback is
transparent to the caller and the UI (same return shape, so templates
don't need to know which path was used).

## Chat Implementation
Real-time messaging uses Flask-SocketIO. Each accepted `Match` maps to a
Socket.IO room named by its `match_id`. On opening `/chat/<match_id>`, the
client emits `join`, joining that room; prior messages are rendered
server-side from the `Message` table on initial page load (avoiding a
race where a client joins before history is fetched). New messages are
emitted as `send_message` events containing match id, sender id/name, and
content; the server persists each message to the `Message` table before
broadcasting `receive_message` to everyone in the room, so message history
is durable even if a party is offline when it's sent — they see it on next
load. Access to a chat room is only exposed in the UI once
`Match.status == 'accepted'`, though a production hardening pass would
also verify server-side (on the `join`/`send_message` handlers) that the
requesting user is actually a party to that match, to prevent id-guessing.

## Notification Flow
Three trigger points call `mailer.send_email()`: (1) a tenant expressing
interest emails the owner, with distinct high-priority copy when the
cached compatibility score exceeds 80; (2) an owner accepting or declining
emails the tenant with the outcome. `mailer.py` uses SMTP (works with any
free-tier provider, e.g. Gmail app passwords) when `SMTP_HOST`/`SMTP_USER`
are configured, and otherwise logs the message to the console — so the
app is fully runnable and demoable without any email credentials, and
notification logic is exercised identically in both modes since the
call site never branches on configuration.

## Data Modelling Notes
Roles (`tenant`/`owner`/`admin`) live on a single `User` table rather than
separate tables, simplifying auth via one Flask-Login model while route
handlers branch on `role` for authorization. `Listing.filled` is a boolean
flag rather than a delete, preserving history for the admin view and any
Match rows that reference it. Foreign keys (`owner_id`, `tenant_id`,
`listing_id`, `match_id`, `sender_id`) keep the schema normalized; scores
and chat messages are the only derived/generated data, and both are
persisted rather than recomputed, which is the main scalability lever
given LLM calls are the most expensive operation in the system.

(≈540 words)

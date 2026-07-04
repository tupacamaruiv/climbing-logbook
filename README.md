# Climbing Logbook

A mobile-first web app for tracking bouldering sessions, individual climbs, and strength training. Log entries from the gym, edit them later, and query the whole history with SQL.

The app is a single static page ([index.html](index.html)) hosted on GitHub Pages. All data lives in a [Supabase](https://supabase.com) Postgres database — the page talks to it directly via supabase-js, behind email/password auth. For architecture and schema details, see [TECHNICAL.md](TECHNICAL.md).

## Features

- **Sessions** — date, location, rating (1–10), notes, media links
- **Climbs** — boulder name, grade, send status (Flash / Send / Attempt / Gave Up), project tracking, attempts, linked to a session
- **Training** — exercise, sets/reps/weight, performance highlights
- **Edit anything** — update or delete past entries from the Edit tab
- **Dynamic dropdowns** — locations and exercises are managed as database tables, not hardcoded lists
- **LLM-queryable** — Claude connects through the Supabase MCP server and runs SQL against the data directly for reports and analysis

## How the Data Is Structured

Five Postgres tables:

| Table | What it holds | Primary key |
|-------|---------------|-------------|
| `sessions` | One row per gym visit | `session_id` (`S`-prefixed) |
| `climbs` | One row per boulder attempt/send, linked to its session | `climb_id` (`C`-prefixed) |
| `training` | One row per strength exercise entry | `training_id` (`T`-prefixed) |
| `locations` | Lookup table for climbing locations | `id` |
| `exercises` | Lookup table for training exercises | `id` |

Climbs reference sessions (`climbs.session_id → sessions.session_id`), so every climb rolls up to the session it happened in. Sessions reference `locations.name` and training references `exercises.name`, keeping naming consistent.

The pre-migration JSON files (the original GitHub-based storage) are archived read-only under [data/archive/](data/archive/).

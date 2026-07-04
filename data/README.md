# Data Storage (archived)

The app now reads and writes Supabase — see `architecture-plan.md`. The JSON
files in `archive/` are a frozen backup of the pre-migration state (migrated
2026-07-04) and are no longer read or written by the app.

- `archive/sessions.json`, `archive/climbs.json`, `archive/training.json` — migrated to the Supabase tables of the same name.
- `archive/exercises.json` — superseded by the `exercises` table.

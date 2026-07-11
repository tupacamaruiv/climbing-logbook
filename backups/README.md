# Database Backups

Point-in-time JSON exports of the climbing logbook's Supabase database, taken
via the Supabase MCP connector (read-only SELECTs). Each dated directory
(`backups/YYYY-MM-DD/`) contains one pretty-printed JSON file per table, with
all columns exactly as stored:

| File             | Table              | Ordered by    |
| ---------------- | ------------------ | ------------- |
| `locations.json` | `public.locations` | `id`          |
| `exercises.json` | `public.exercises` | `id`          |
| `sessions.json`  | `public.sessions`  | `session_id`  |
| `climbs.json`    | `public.climbs`    | `climb_id`    |
| `training.json`  | `public.training`  | `training_id` |

## Why these exist

See GitHub issue #47 ("no backup path"):

- Free-tier Supabase **pauses projects after ~1 week of inactivity** and has
  **no point-in-time recovery**.
- The app **hard-deletes** rows with no undo.

Without these snapshots, a bad bulk edit, an accidental delete, or a paused/
reclaimed project would mean permanent data loss. Committing snapshots to git
gives versioned, offsite (GitHub) copies for free.

## Taking a new snapshot

Ask Claude Code:

> snapshot the Supabase tables into `backups/<today>/` like the existing ones

It runs one query per table of the form:

```sql
SELECT COALESCE(json_agg(t ORDER BY <pk>), '[]'::json)
FROM (SELECT * FROM public.<table>) t;
```

and writes each result as pretty-printed JSON. Sanity-check the row counts
against the previous snapshot before committing (they should only grow, apart
from deliberate deletions).

## Restoring

Two options:

1. **SQL editor**: for each affected table, `TRUNCATE` it (or delete the bad
   rows) and re-insert from the snapshot, e.g. with
   `INSERT INTO public.<table> SELECT * FROM json_populate_recordset(NULL::public.<table>, '<contents of file>');`
   Restore `sessions` before `climbs` if foreign keys are enforced.
2. **Claude Code**: point it at the snapshot directory and ask it to restore a
   table (or specific rows) from the JSON.

## Cadence

Automated: a scheduled Claude Code routine ("Climbing logbook — weekly DB
keep-alive + monthly backup snapshot", manageable at
<https://claude.ai/code/routines>) runs every Monday. It pings the database
weekly (free-tier keep-alive) and commits a fresh snapshot directory the
first week of each month.

Manual: also take a snapshot **before any bulk edit or migration**.

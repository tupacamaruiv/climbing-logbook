# Climbing Logbook — Supabase Migration Plan

**Goal:** Replace GitHub JSON files as the data layer while keeping the existing web app as the logging interface. Maintain SessionID → ClimbID relationships. Support dynamic updates to Locations and Exercises. Enable native LLM querying for reports, analysis, and charts on mobile.

---

## ⬅️ RESUME HERE (as of 2026-07-04, evening)

Steps 1–6 are done and verified. Everything below is what's left, in order. Items 1–3 are manual (dashboard/browser); Claude can help with 4–6.

### 1. Paste the anon key ✅ Done 2026-07-04
Anon key pasted into `index.html` (~line 560) and committed — verified it's the anon-role key, not service_role.

### 2. First sign-in
Open the app — it shows a sign-in form (Option B RLS). Sign in as the Supabase auth user `ceparedes7@gmail.com` (created 2026-06-20; reset the password in Supabase → Authentication → Users if forgotten). The session persists in localStorage, so this is one-time per browser/device — remember to do it once on the phone too.

### 3. Step 8 — end-to-end test
REST-level integrity checks already passed (2026-07-04); what's left is the live browser test:
- Page load: location + exercise dropdowns populate (proves reads + auth work).
- Log a real session, a climb attached to it, and a training entry (proves all three insert paths).
- Edit and delete one test entry (proves update/delete paths).
- Confirm the rows in Supabase → Table Editor. Note: test rows are in the DB only — the JSON files are frozen, so deleting test rows via the app's edit panel is the cleanup.

### 4. Step 7 — connect Supabase MCP to the Claude.ai project
Done on claude.ai (not in this repo): claude.ai → Settings → Connectors → add the official Supabase connector (`mcp.supabase.com`), authorize it against this project (`albnsouvcxmchiqolggc`), then enable it in the climbing project. Test with a query like "how many V6s have I sent?" — it should run SQL against `climbs` directly.

### 5. Step 9 — archive the JSON files ✅ Done 2026-07-04
All four JSON files moved to `data/archive/` (via `git mv`, staged but not yet committed). `migrate.py` paths updated to match, so it can still be rerun; `data/README.md` updated to say the folder is a frozen pre-migration backup.

### 6. Cleanup + commit
- **Delete `.env.migration`** once you're confident you won't rerun `migrate.py` — it holds the service-role key in plaintext. (If it ever leaks, rotate the key in Supabase dashboard → Project Settings → API.)
- Commit the pending work: modified `index.html` + `architecture-plan.md` + `data/README.md`, new `migrate.py` + `.gitignore`, and the `data/*.json` → `data/archive/` moves (already staged). The anon key is safe to commit (it's public by design; RLS is the protection) — the service-role key is not, and `.gitignore` already covers `.env.migration`.

### State notes (context for whoever picks this up)
- **Data migration (Step 4) ran clean on 2026-07-04**: sessions 108, climbs 57, training 169 — 0 errors, counts verified. Post-checks: 0 orphan climbs, 4 training rows with `updated_at`, no empty-string media, lookup tables intact (4 locations, 18 exercises).
- `migrate.py` is safe to rerun (upserts on primary keys) — but only before new entries are logged via the app; after that, a rerun would overwrite newer edits of migrated rows with stale JSON values (new rows are untouched).
- `index.html` is fully Supabase-backed via supabase-js v2 (CDN): all GitHub API code removed (submit handlers, edit/delete flows, reads, dropdowns, token setup UI). The old GitHub Setup panel is now the sign-in panel. Auth failures on writes route back to sign-in.
- Column renames to remember when querying: `videos`→`media`, `timestamp`→`created_at`, `lastUpdated`→`updated_at`; `rpe` and `gradeSystem` were intentionally dropped.

---

## Current Data Architecture

Four flat JSON files in a GitHub repo. Schema derived from live data:

### sessions.json
```json
{
  "sessionId": "S1758849068880",
  "date": "2025-09-26",
  "location": "Peak Boulders",
  "rating": 8,
  "notes": "...",
  "videos": "https://...",
  "timestamp": "2025-09-26T01:11:08.880Z",
  "lastUpdated": "2025-09-27T11:16:08.094Z"
}
```

### climbs.json
```json
{
  "climbId": "C1758849205145",
  "sessionId": "S1758849068880",
  "boulderName": "Tighty Whities",
  "grade": "V6",
  "sendStatus": "Send",             // "Flash", "Send", "Attempt", "Gave Up"
  "isProject": true,
  "attempts": 2,
  "performanceHighlight": false,
  "notes": "...",
  "videos": "https://...",
  "timestamp": "...",
  "lastUpdated": "..."
}
```

### training.json
```json
{
  "trainingId": "T1758933957563",
  "date": "2025-09-24",
  "exercise": "20mm Lift",
  "sets": 3,                        // optional
  "reps": 5,                        // optional
  "weight": 31,
  "performanceHighlight": false,
  "notes": "...",
  "timestamp": "..."
}
```

### exercises.json
A flat array of exercise name strings. Replaced by the `exercises` table.

### Implicit lookup tables (currently hardcoded in index.html)
- **Locations**: Peak Boulders, Peak Midlo Board, Triangle Board, Triangle Boulders, + others
- **Exercises**: loaded from exercises.json at runtime
- **Send statuses**: Flash, Send, Attempt, Gave Up

---

## Database Schema

Supabase (hosted Postgres) with a REST API and official MCP server. The web app POSTs to the Supabase REST API instead of committing JSON. Claude queries via the Supabase MCP natively.

```sql
-- Lookup tables (dynamic, user-managed)
CREATE TABLE locations (
  id        SERIAL PRIMARY KEY,
  name      TEXT UNIQUE NOT NULL,
  active    BOOLEAN DEFAULT true
);

CREATE TABLE exercises (
  id        SERIAL PRIMARY KEY,
  name      TEXT UNIQUE NOT NULL,
  category  TEXT,         -- 'finger', 'barbell', 'board', etc.
  active    BOOLEAN DEFAULT true
);

-- Core tables
CREATE TABLE sessions (
  session_id    TEXT PRIMARY KEY,   -- preserves existing S-prefixed IDs
  date          DATE NOT NULL,
  location      TEXT REFERENCES locations(name),
  rating        SMALLINT CHECK (rating BETWEEN 1 AND 10),
  notes         TEXT,
  media         TEXT,               -- renamed from "videos" in the app
  created_at    TIMESTAMPTZ NOT NULL,
  updated_at    TIMESTAMPTZ
);

CREATE TABLE climbs (
  climb_id              TEXT PRIMARY KEY,   -- preserves existing C-prefixed IDs
  session_id            TEXT REFERENCES sessions(session_id),
  boulder_name          TEXT NOT NULL,
  grade                 TEXT,               -- grade encodes system (V6 = V-scale, B0 = B-scale)
  send_status           TEXT CHECK (send_status IN ('Flash', 'Send', 'Attempt', 'Gave Up')),
  is_project            BOOLEAN DEFAULT false,
  attempts              SMALLINT,
  performance_highlight BOOLEAN DEFAULT false,
  notes                 TEXT,
  media                 TEXT,               -- renamed from "videos" in the app
  created_at            TIMESTAMPTZ NOT NULL,
  updated_at            TIMESTAMPTZ
);

CREATE TABLE training (
  training_id           TEXT PRIMARY KEY,  -- preserves existing T-prefixed IDs
  date                  DATE NOT NULL,
  exercise              TEXT REFERENCES exercises(name),
  sets                  SMALLINT,
  reps                  SMALLINT,
  weight                NUMERIC,
  performance_highlight BOOLEAN DEFAULT false,
  notes                 TEXT,
  created_at            TIMESTAMPTZ NOT NULL,
  updated_at            TIMESTAMPTZ
);
```

---

## Migration Steps

| # | Step | Status |
|---|------|--------|
| 1 | Create Supabase project | ✅ Done |
| 2 | Run table creation SQL in Supabase SQL Editor | ✅ Done — Option B (authenticated-only) RLS |
| 3 | Seed lookup tables (locations + exercises) | ✅ Done — 4 locations, 18 exercises, categories NULL for now |
| 4 | Install Python, then run migration script for existing JSON records | ✅ Done 2026-07-04 — 108/57/169 rows migrated, 0 errors, counts + integrity verified |
| 5 | Update web app submit handlers (3 forms: session, climb, training) | ✅ Done 2026-07-04 — supabase-js + sign-in flow; edit/delete flows converted too. 🔶 Blocked on pasting anon key into `index.html` |
| 6 | Update web app dropdowns to load from Supabase | ✅ Done 2026-07-04 — locations + exercises DB-driven (`active=true`, ordered by name) |
| 7 | Connect Supabase MCP to Claude.ai project | |
| 8 | End-to-end test with a live session log | 🔶 REST-level integrity checks passed; live browser test blocked on anon key |
| 9 | Archive GitHub JSON files (keep as backup, stop writing to them) | ✅ Done 2026-07-04 — moved to `data/archive/`, migrate.py paths updated |

---

## Row Level Security — ✅ Decided and applied: Option B (authenticated-only)

Resolved at Step 2: RLS is enabled on all five tables with Option B policies. Kept below for reference — Option B has a follow-up task at Step 5 (create a Supabase user and add the silent sign-in to the web app).

**Option A — Anon-open (simpler):**
Enable RLS with a permissive policy that allows all operations for the anon key. Functionally identical to no RLS, but the flag is on and the policy can be tightened later. Anyone who finds the anon key in the page source can read and write your data.

```sql
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE climbs ENABLE ROW LEVEL SECURITY;
ALTER TABLE training ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow all" ON sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow all" ON climbs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow all" ON training FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow all" ON locations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow all" ON exercises FOR ALL USING (true) WITH CHECK (true);
```

**Option B — Authenticated-only (recommended):**
Policies require a logged-in Supabase user. You sign in once with your own email/password; the session is stored in localStorage. The anon key in the page source becomes useless to anyone else.

```sql
-- Same ENABLE statements, then:
CREATE POLICY "authenticated only" ON sessions FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "authenticated only" ON climbs FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "authenticated only" ON training FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "authenticated only" ON locations FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "authenticated only" ON exercises FOR ALL USING (auth.role() = 'authenticated');
```

The app then silently signs in on load (credentials stored in localStorage):
```javascript
await supabase.auth.signInWithPassword({ email: '...', password: '...' });
```

**Recommendation: Option B.** ~30 minutes of extra work at step 5, and it's the only option that actually protects the data from anyone who views the page source.

---

## Web App Changes (Step 5)

Replace the GitHub commit handler with Supabase REST calls. The `videos` field is renamed to `media` in the process.

> **⚠️ Option B RLS is live**, so the raw-anon-key pattern below will be rejected (401/permission denied) as-is. At Step 5, also: create a user in Supabase → Authentication → Users, sign in via `supabase.auth.signInWithPassword(...)` on page load, and send the resulting session's access token as the `Authorization: Bearer` value (the `supabase-js` client does this automatically — simplest path is to use it instead of raw `fetch`). The `apikey` header stays the anon key either way.

**Current pattern:**
```javascript
await commitToGitHub('data/sessions.json', updatedData, sha);
```

**New pattern:**
```javascript
const SUPABASE_URL = 'https://your-project.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key';

async function insertSession(entry) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/sessions`, {
    method: 'POST',
    headers: {
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=representation'
    },
    body: JSON.stringify({
      session_id: entry.sessionId,
      date: entry.date,
      location: entry.location,
      rating: entry.rating,
      notes: entry.notes,
      media: entry.media,
      created_at: entry.timestamp
    })
  });
  return res.json();
}
```

Same pattern applies for `climbs` and `training` tables.

### Dynamic Locations and Exercises (Step 6)

Replace hardcoded `<option>` elements with database-driven dropdowns:

```javascript
async function loadLocations() {
  const res = await fetch(
    `${SUPABASE_URL}/rest/v1/locations?active=eq.true&order=name`,
    { headers: { 'apikey': SUPABASE_ANON_KEY } }
  );
  const locations = await res.json();
  const select = document.getElementById('location');
  locations.forEach(loc => {
    select.innerHTML += `<option value="${loc.name}">${loc.name}</option>`;
  });
}
```

---

## Step 4 Details

### Install Python on Windows

✅ Done 2026-07-04 — Python 3.12.10 installed via `winget install Python.Python.3.12` and added to the user PATH (open a **new** terminal for `python` to resolve). No `pip install` needed; `migrate.py` uses only the standard library.

### Data Notes (updated 2026-07-04 after full validation)

**Record counts in the JSON files (data grew since the plan was first written):**
- `sessions.json`: 108 records
- `climbs.json`: 57 records
- `training.json`: 169 records
- `exercises.json`: 18 records (already seeded in Step 3 — skip this file)

**Validation results (2026-07-04):** all locations, exercises, and send statuses match the seeded lookup tables and CHECK constraints; no FK violations, no duplicate IDs, no missing required fields. The data migrates clean.

**Data quirks:**
- ~~Sessions `rpe` always equals `rating`~~ Wrong — 57 of 108 sessions have `rpe` ≠ `rating`, and the 8 newest sessions have no `rpe` field at all. **Decision (2026-07-04): keep `rating` only; all `rpe` values are intentionally dropped in the migration.**
- 4 training records have a `lastUpdated` field; the migration maps it to `updated_at` (the original plan draft missed this).
- Empty `videos` strings (`""`) are migrated as `null` (the `media` column is `TEXT`, null is cleaner than empty string).

**Supabase credentials needed:**
- Project URL: `https://xxxx.supabase.co` (from Supabase dashboard → Project Settings → API)
- **Service role key** (not the anon key) — service role bypasses RLS, required for bulk migration before auth is wired up in the app. Find it in Project Settings → API → "service_role" key.

---

## Migration Script (Step 4)

**The live script is [`migrate.py`](migrate.py) in the repo root** — it supersedes the draft below. Differences from the draft: stdlib-only (no `pip install requests` needed), credentials read from git-ignored `.env.migration` instead of hardcoded, upserts on primary key (safe to rerun), training remap includes `updated_at`, `rpe` dropped per the 2026-07-04 decision (rating is the kept field), and automatic row-count verification at the end.

Fill in `.env.migration`, then run from the repo root: `python migrate.py`

**Expected output after a clean run:** `sessions: 108, climbs: 57, training: 169` inserted, 0 errors, all counts verified.

<details>
<summary>Original draft script (superseded by migrate.py — kept for reference)</summary>

```python
import json, requests

SUPABASE_URL = 'https://your-project.supabase.co'   # replace
SERVICE_ROLE_KEY = 'your-service-role-key'           # replace — NOT the anon key

HEADERS = {
    'apikey': SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json'
}

def clean(value):
    """Convert empty strings to None so they store as NULL."""
    if value == '':
        return None
    return value

def migrate(file, table, remap):
    with open(file) as f:
        records = json.load(f)
    errors = []
    for r in records:
        payload = {}
        for col, key in remap.items():
            val = clean(r.get(key))
            if val is not None:
                payload[col] = val
        res = requests.post(f'{SUPABASE_URL}/rest/v1/{table}',
                            json=payload, headers=HEADERS)
        if not res.ok:
            errors.append((r.get(list(remap.values())[0]), res.status_code, res.text))
    print(f'{table}: {len(records) - len(errors)} inserted, {len(errors)} errors')
    for e in errors:
        print(f'  ERROR {e[1]} on {e[0]}: {e[2]}')

migrate('data/sessions.json', 'sessions', {
    'session_id':  'sessionId',
    'date':        'date',
    'location':    'location',
    'rating':      'rating',     # rpe field is ignored — same value, rating is canonical
    'notes':       'notes',
    'media':       'videos',     # renamed to media
    'created_at':  'timestamp',
    'updated_at':  'lastUpdated'
})

migrate('data/climbs.json', 'climbs', {
    'climb_id':             'climbId',
    'session_id':           'sessionId',
    'boulder_name':         'boulderName',
    'grade':                'grade',         # gradeSystem dropped — encoded in grade value
    'send_status':          'sendStatus',
    'is_project':           'isProject',
    'attempts':             'attempts',
    'performance_highlight':'performanceHighlight',
    'notes':                'notes',
    'media':                'videos',        # renamed to media
    'created_at':           'timestamp',
    'updated_at':           'lastUpdated'
})

migrate('data/training.json', 'training', {
    'training_id':          'trainingId',
    'date':                 'date',
    'exercise':             'exercise',
    'sets':                 'sets',
    'reps':                 'reps',
    'weight':               'weight',
    'performance_highlight':'performanceHighlight',
    'notes':                'notes',
    'created_at':           'timestamp'
})
```

</details>

After running, verify counts in Supabase → Table Editor for each table (migrate.py also does this automatically).

---

## Claude Integration (Step 7)

Supabase has an official MCP server (`mcp.supabase.com`). Once connected:

- Claude queries tables directly via SQL — no `web_fetch`, no token truncation
- Filtered queries: `SELECT * FROM training WHERE exercise = '20mm Lift' ORDER BY date DESC LIMIT 10`
- Joins: `SELECT s.date, s.location, c.boulder_name, c.grade, c.send_status FROM sessions s JOIN climbs c ON s.session_id = c.session_id WHERE c.is_project = true`
- Reports and charts: Claude's code execution runs Python/pandas against query results

---

## Open Questions

1. **GitHub as backup:** Keep the GitHub JSON files as a read-only archive after migration, or deprecate entirely? Keeping them risks accidental double-logging if the old write path isn't fully disabled.

2. **Offline logging:** Neither option adds offline support. If logging in a gym with poor WiFi is a pain point, a local-first approach (IndexedDB + sync) would need to be layered on later.

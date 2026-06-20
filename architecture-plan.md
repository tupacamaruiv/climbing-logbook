# Climbing Logbook — Supabase Migration Plan

**Goal:** Replace GitHub JSON files as the data layer while keeping the existing web app as the logging interface. Maintain SessionID → ClimbID relationships. Support dynamic updates to Locations and Exercises. Enable native LLM querying for reports, analysis, and charts on mobile.

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
| 4 | Install Python, then run migration script for existing JSON records | ⬅️ Next — see Step 4 details below |
| 5 | Update web app submit handlers (3 forms: session, climb, training) | |
| 6 | Update web app dropdowns to load from Supabase | |
| 7 | Connect Supabase MCP to Claude.ai project | |
| 8 | End-to-end test with a live session log | |
| 9 | Archive GitHub JSON files (keep as backup, stop writing to them) | |

---

## Open Decision: Row Level Security

RLS should be enabled on all tables. The question is which policy to use.

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

Python and Node.js are not installed on this machine. The migration script requires Python. Install it first:

1. Go to **python.org/downloads** and click "Download Python 3.x.x" (latest stable)
2. Run the installer `.exe`
3. **Critical:** On the first screen, check **"Add Python to PATH"** before clicking Install Now
4. Click "Install Now" and let it complete
5. Open a new PowerShell window and verify: `python --version`
6. Install the `requests` library: `pip install requests`

### Data Notes (discovered during migration planning)

**Record counts in the JSON files:**
- `sessions.json`: 102 records
- `climbs.json`: 57 records
- `training.json`: 158 records
- `exercises.json`: 18 records (already seeded in Step 3 — skip this file)

**Data quirks to be aware of:**
- Sessions have both an `rpe` field and a `rating` field with the same value. The schema uses `rating`. The `rpe` field is dropped during migration.
- Empty `videos` strings (`""`) are migrated as `null` (the `media` column is `TEXT`, null is cleaner than empty string). The migration script handles this with `or None`.

**Supabase credentials needed:**
- Project URL: `https://xxxx.supabase.co` (from Supabase dashboard → Project Settings → API)
- **Service role key** (not the anon key) — service role bypasses RLS, required for bulk migration before auth is wired up in the app. Find it in Project Settings → API → "service_role" key.

---

## Migration Script (Step 4)

Fill in your credentials at the top, then run from the repo root:
`python migrate.py`

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

**Expected output after a clean run:**
```
sessions: 102 inserted, 0 errors
climbs: 57 inserted, 0 errors
training: 158 inserted, 0 errors
```

After running, verify counts in Supabase → Table Editor for each table.

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

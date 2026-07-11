# Climbing Logbook — Technical Documentation

## Technology Stack

### Frontend
- **HTML5 / CSS3 / Vanilla JavaScript (ES6+)** — single-file app in `index.html`, no build step
- **supabase-js v2** — loaded from the jsDelivr CDN, handles all database reads/writes and auth
- **Mobile-first responsive design** — built for logging at the gym

### Backend & Storage
- **Supabase (hosted Postgres)** — all climbing data lives in five tables
- **Supabase Auth** — email/password sign-in; the session persists in localStorage so sign-in is a one-time step per device
- **Row Level Security** — enabled on every table with authenticated-only policies, so the anon key embedded in the page source grants no access by itself

### Hosting & Integrations
- **GitHub Pages** — serves the static frontend; deploys automatically on push to `main`
- **Supabase MCP server** (`mcp.supabase.com`) — lets Claude query the database directly with SQL for reports, analysis, and charts

## System Architecture

```
┌────────────┐   HTTPS    ┌──────────────────┐  supabase-js   ┌──────────────────┐
│   Mobile   │ ─────────► │  Static web app  │ ─────────────► │     Supabase     │
│    user    │            │  (GitHub Pages)  │   REST + Auth  │    (Postgres)    │
└────────────┘            └──────────────────┘                └──────────────────┘
                                                                       ▲
┌────────────┐        Supabase MCP server (SQL)                        │
│   Claude   │ ────────────────────────────────────────────────────────┘
└────────────┘
```

Auth flow: on load the app reuses a persisted Supabase session from localStorage if one exists; otherwise it shows a sign-in panel and calls `supabase.auth.signInWithPassword(...)`. Every subsequent read/write carries the authenticated user's access token, which is what the RLS policies require.

## Database Schema

```sql
-- Lookup tables (dynamic, user-managed — drive the app's dropdowns)
CREATE TABLE locations (
  id        SERIAL PRIMARY KEY,
  name      TEXT UNIQUE NOT NULL,
  active    BOOLEAN DEFAULT true
);

CREATE TABLE exercises (
  id        SERIAL PRIMARY KEY,
  name      TEXT UNIQUE NOT NULL,
  active    BOOLEAN DEFAULT true
);

-- Core tables
CREATE TABLE sessions (
  session_id    TEXT PRIMARY KEY,   -- S-prefixed IDs, e.g. S1758849068880
  date          DATE NOT NULL,
  location      TEXT REFERENCES locations(name),
  rating        SMALLINT CHECK (rating BETWEEN 1 AND 10),
  notes         TEXT,
  media         TEXT,
  created_at    TIMESTAMPTZ NOT NULL,
  updated_at    TIMESTAMPTZ
);

CREATE TABLE climbs (
  climb_id              TEXT PRIMARY KEY,   -- C-prefixed IDs
  session_id            TEXT REFERENCES sessions(session_id),
  boulder_name          TEXT NOT NULL,
  grade                 TEXT,               -- grade encodes the system (V6 = V-scale, B0 = B-scale)
  send_status           TEXT CHECK (send_status IN ('Flash', 'Send', 'Attempt', 'Gave Up')),
  is_project            BOOLEAN DEFAULT false,
  attempts              SMALLINT,
  performance_highlight BOOLEAN DEFAULT false,
  notes                 TEXT,
  media                 TEXT,
  created_at            TIMESTAMPTZ NOT NULL,
  updated_at            TIMESTAMPTZ
);

CREATE TABLE training (
  training_id           TEXT PRIMARY KEY,   -- T-prefixed IDs
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

### Relationships

- `climbs.session_id → sessions.session_id` — every climb belongs to a session
- `sessions.location → locations.name` — locations are constrained to the lookup table
- `training.exercise → exercises.name` — exercises are constrained to the lookup table

### Row Level Security

RLS is enabled on all five tables with a single policy each:

```sql
CREATE POLICY "authenticated only" ON <table>
  FOR ALL USING (auth.role() = 'authenticated');
```

The anon (public) key in the page source can therefore only be used to attempt sign-in — all data access requires a valid Supabase user session.

## Data Flow

All CRUD goes through the supabase-js client:

```javascript
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Insert a session
await sb.from('sessions').insert({
  session_id: 'S' + Date.now(),
  date, location, rating, notes, media,
  created_at: new Date().toISOString()
});

// Load dropdown options
await sb.from('locations').select('name').eq('active', true).order('name');

// Edit / delete
await sb.from('climbs').update({ notes, media, updated_at: ... }).eq('climb_id', id);
await sb.from('training').delete().eq('training_id', id);
```

Dropdowns for location and exercise are loaded from the `locations` and `exercises` tables (`active = true`, ordered by name), so adding a new gym or exercise is a database row, not a code change.

## Claude Integration

The Supabase MCP server gives Claude direct SQL access to the database:

```sql
-- Project pipeline
SELECT s.date, s.location, c.boulder_name, c.grade, c.send_status
FROM sessions s JOIN climbs c ON s.session_id = c.session_id
WHERE c.is_project = true;

-- Training history for one exercise
SELECT * FROM training WHERE exercise = '20mm Lift' ORDER BY date DESC LIMIT 10;
```

Reports and charts run against live query results — no file fetching or token-limit truncation.

## Migration History

The app originally stored data as JSON files (`sessions.json`, `climbs.json`, `training.json`) committed to this GitHub repo via the GitHub Contents API. In July 2026 the data layer was migrated to Supabase:

- All rows were migrated with IDs preserved (the `S`/`C`/`T`-prefixed keys)
- Column renames: `videos` → `media`, `timestamp` → `created_at`, `lastUpdated` → `updated_at`
- Dropped fields: `rpe` (sessions — `rating` is the kept metric) and `gradeSystem` (climbs — the system is encoded in the grade value itself)
- The original JSON files are archived read-only under `data/archive/` and are no longer written to

## File Structure

```
climbing-logbook/
├── index.html          # The entire application (markup, styles, logic)
├── README.md           # Project overview and data structure
├── TECHNICAL.md        # This document
└── data/
    └── archive/        # Pre-migration JSON files (read-only backup)
```

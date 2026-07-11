-- Run this once in the Supabase SQL editor (or via MCP with read-only mode off).
-- Covers GitHub issues #46 (schema hardening) and #41 (one-time date-skew correction).
-- Safe to re-run: every statement is idempotent or self-limiting.

-- ============================================================
-- Issue #46: schema hardening
-- ============================================================

-- 1. DB-owned timestamps: created_at defaults to now(), updated_at maintained by trigger
ALTER TABLE public.sessions ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE public.climbs   ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE public.training ALTER COLUMN created_at SET DEFAULT now();

CREATE EXTENSION IF NOT EXISTS moddatetime WITH SCHEMA extensions;

DROP TRIGGER IF EXISTS set_updated_at ON public.sessions;
DROP TRIGGER IF EXISTS set_updated_at ON public.climbs;
DROP TRIGGER IF EXISTS set_updated_at ON public.training;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.sessions FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);
CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.climbs   FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);
CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.training FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);

-- 2. Rename-safe natural-key FKs: renaming a location/exercise cascades to history
ALTER TABLE public.sessions DROP CONSTRAINT sessions_location_fkey;
ALTER TABLE public.sessions ADD CONSTRAINT sessions_location_fkey
  FOREIGN KEY (location) REFERENCES public.locations(name) ON UPDATE CASCADE;
ALTER TABLE public.training DROP CONSTRAINT training_exercise_fkey;
ALTER TABLE public.training ADD CONSTRAINT training_exercise_fkey
  FOREIGN KEY (exercise) REFERENCES public.exercises(name) ON UPDATE CASCADE;

-- 3. Covering indexes for the three FKs (performance advisor)
CREATE INDEX IF NOT EXISTS idx_climbs_session_id ON public.climbs(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_location ON public.sessions(location);
CREATE INDEX IF NOT EXISTS idx_training_exercise ON public.training(exercise);

-- ============================================================
-- Issue #41: one-time correction of UTC-skewed dates
-- ============================================================
-- Skew signature: the row's date equals the UTC calendar date of creation while
-- the local (America/New_York) date at creation was the day before — i.e. the
-- form's old UTC-based "today" default stamped an evening entry with tomorrow.
-- Audited 2026-07-11: matches exactly 6 sessions + 2 training rows.
-- (Back-filled entries — date before the created date — do NOT match and are untouched.)

UPDATE public.sessions
SET date = date - 1
WHERE date = (created_at AT TIME ZONE 'UTC')::date
  AND (created_at AT TIME ZONE 'America/New_York')::date = date - 1;

UPDATE public.training
SET date = date - 1
WHERE date = (created_at AT TIME ZONE 'UTC')::date
  AND (created_at AT TIME ZONE 'America/New_York')::date = date - 1;

-- After applying this file, the client-set created_at/updated_at lines in index.html
-- become redundant (DB defaults + trigger take over) and can be removed — they are
-- harmless to keep, but removing them before applying this file would break inserts.

-- Verify: both queries should return 0 rows afterwards
-- SELECT session_id  FROM public.sessions WHERE date = (created_at AT TIME ZONE 'UTC')::date AND (created_at AT TIME ZONE 'America/New_York')::date = date - 1;
-- SELECT training_id FROM public.training WHERE date = (created_at AT TIME ZONE 'UTC')::date AND (created_at AT TIME ZONE 'America/New_York')::date = date - 1;

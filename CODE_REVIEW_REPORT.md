# Code Review Report — Climbing Logbook

**Date:** 2026-07-06
**Scope:** Full review of `index.html` (app), live Supabase schema/RLS/indexes, Supabase security & performance advisors, architecture and design assumptions.
**Method:** Two parallel review agents (bug/security hunt, senior architecture review) plus a direct schema review against the live database. High-impact findings verified against the code before filing.

**Outcome:** 8 new GitHub issues filed, 1 reopened — all with remediation plans.

---

## Issues Filed

| # | Title | Severity | Status |
|---|-------|----------|--------|
| [#39](https://github.com/tupacamaruiv/climbing-logbook/issues/39) | Any authenticated user has full CRUD — disable public signups, pin RLS to your uid | Critical | ✅ Fixed 2026-07-11 |
| [#40](https://github.com/tupacamaruiv/climbing-logbook/issues/40) | Stale edit selection survives type switch — Delete can remove the wrong row | High | ✅ Fixed 2026-07-11 (251179b) |
| [#41](https://github.com/tupacamaruiv/climbing-logbook/issues/41) | "Today" computed in UTC — evening entries dated tomorrow | High | ✅ Fixed 2026-07-11 — code (251179b) + 8 skewed rows corrected in DB |
| [#42](https://github.com/tupacamaruiv/climbing-logbook/issues/42) | supabase-js loaded with floating `@2` tag, no SRI | Medium | ✅ Fixed 2026-07-11 — pinned 2.110.2 + SRI |
| [#43](https://github.com/tupacamaruiv/climbing-logbook/issues/43) | Numeric inputs unvalidated — NaN becomes NULL; edit can wipe weight | Medium | ✅ Fixed 2026-07-11 (251179b) |
| [#45](https://github.com/tupacamaruiv/climbing-logbook/issues/45) | Error-handling gaps — silent loader failures, uncaught exceptions, raw FK errors | Medium | ✅ Fixed 2026-07-11 (251179b) |
| [#46](https://github.com/tupacamaruiv/climbing-logbook/issues/46) | Schema hardening — DB-owned timestamps, rename-safe FKs, covering indexes | Medium | ✅ Fixed 2026-07-11 — migration applied via SQL editor; client timestamps removed |
| [#47](https://github.com/tupacamaruiv/climbing-logbook/issues/47) | No backup path — Supabase is the single copy of the data | Medium | ✅ Fixed 2026-07-11 — snapshot in `backups/` + weekly cloud routine |
| [#44](https://github.com/tupacamaruiv/climbing-logbook/issues/44) | Editing a session with unset rating silently writes 5 | Low | ✅ Fixed 2026-07-11 (251179b) |
| [#38](https://github.com/tupacamaruiv/climbing-logbook/issues/38) | Reopened — `data/nul` has reappeared in the working tree | Chore | ✅ Fixed 2026-07-11 — deleted + gitignored |

---

## Resolution Pass — 2026-07-11

All nine open issues were worked in one pass (commits `0f7767f`…`0f6c8d8` plus follow-ups) and are now closed. The DB work — the #46 migration, the #41 date correction, and the data-quality cleanups — lives in [`db/2026-07-11_schema_hardening_and_date_fix.sql`](db/2026-07-11_schema_hardening_and_date_fix.sql) and was **applied via the Supabase SQL editor on 2026-07-11** (the MCP connector is read-only), then verified: 0 skewed dates remain, 3 `moddatetime` triggers installed, both natural-key FKs cascade on update, all 3 covering indexes present, `created_at` defaults on all 3 core tables. A first full backup snapshot lives in `backups/2026-07-11/`, and a scheduled cloud routine now pings the DB weekly (free-tier keep-alive) and commits a monthly snapshot.

### Data-quality findings from the backup review

The snapshot pass surfaced four small data observations (none are backup problems):

1. **Mojibake in one climb note** — ✅ fixed. "Heartfelt but Unserious" (`C1766513669571`) contained a multiply-encoded apostrophe ("haven[ÃÂ…]t") corrupted in the database itself; the note now reads "haven't". (Fun fact: the first fix attempt no-op'd because Ã/Â count as *alphabetic* in Unicode, so a `[^[:alpha:]]` character class refused to match them.)
2. **`exercises.category` was NULL on all 18 rows** and never read by the app — ✅ column dropped; removed from TECHNICAL.md's schema listing. (The 2026-07-11 backup snapshot still shows it, faithfully, as a point-in-time export.)
3. **"Bear Hug" is logged at B2 in one session and B3 in another** — possibly a regrade, possibly a typo. Left as-is; worth a manual glance.
4. **`training.sets`/`reps` are NULL on many rows** (e.g. all "20mm Lift" entries) — consistent with intentional weight-only logging; no action.

---

## The Three That Matter Most

### #39 — The auth boundary is "anyone with a Supabase account on your project"

Every RLS policy is just `auth.role() = 'authenticated'` with no owner scoping (verified via `pg_policies`). Supabase enables email signups by default, and the anon key in the page source is all anyone needs to call the signup endpoint directly. If signups are enabled (unverified — it's a dashboard setting), a stranger can register an account and read or wipe every table.

**Fix:** Disable public signups (Dashboard → Auth → Providers → Email), then rewrite the five policies to `(select auth.uid()) = '<your-uuid>'::uuid` with a matching `WITH CHECK`. The `(select ...)` form also resolves the advisor's per-row `auth.role()` re-evaluation warning on all five tables. Also enable leaked-password protection (flagged by the security advisor), add a Sign Out button, and latch `signIn()` against double invocation.

**Resolved 2026-07-11:** All five RLS policies rewritten to `owner only` pinned to the owner's uid with matching `WITH CHECK` (verified live via `pg_policies`); public signups disabled in the dashboard; Sign Out button and `signIn()` in-flight latch added to `index.html`. Leaked-password protection skipped — not available on the free tier, and moot with signups disabled and owner-pinned policies.

### #41 — Dates are probably being corrupted right now

"Today" is computed as `new Date().toISOString().split('T')[0]` — the **UTC** calendar date — in four places (form defaults, form reset, submit fallback, session-dropdown filter). From 8pm ET / 5pm PT onward, the pre-filled date is tomorrow. For an evening-activity logger this is systematic, ongoing skew that gets harder to repair the longer it runs.

**Fix:** One helper — `const localToday = () => new Date().toLocaleDateString('en-CA');` — used at all four call sites, plus a one-time SQL audit comparing `date` vs `created_at` in the local timezone to find already-shifted rows (query in the issue).

### #40 — A delete bug that removes the wrong row

`loadEditData()` never clears `selectedEditItem` when the edit-type dropdown changes. Select a climb under "Recent Climbs," switch the dropdown to "Recent Sessions," click Delete: the stale climb object still has a `sessionId` property (mapped from its `session_id` column), so the app runs `delete from sessions where session_id = <the climb's parent session>` — behind a confirmation dialog that reads "delete this session from undefined at undefined."

**Fix:** Call `clearEditForm()` unconditionally at the top of `loadEditData()`, and record the entity type on the selection itself so `updateEntry`/`confirmDelete` can never mix type and item.

---

## Other Bugs & Security Findings

- **Supply chain (#42):** `<script src=".../supabase-js@2">` floats across every future 2.x publish with no SRI hash. The likeliest bite is a breaking minor release taking the app down on a random Tuesday; the worst case is a compromised release executing with full DB access. Pin the exact version and add an `integrity` attribute.
- **Numeric validation (#43):** There is no `<form>` element, so `required`/`min` are never enforced. `parseInt('')` → `NaN` → JSON-serialized as `null`: clearing Attempts saves a climb with `attempts = null`; clearing Working Weight in the training *edit* form silently wipes the stored weight (`updateEntry` lacks the `isNaN` check that `submitTraining` has).
- **Error handling (#45):** The four reference-data loaders fail with `console.log` only — with an expired refresh token the app renders with empty required dropdowns and no message. `guardedWrite` has no `catch`, so thrown exceptions vanish while the button resets as if the write succeeded. Deleting a session with climbs surfaces a raw Postgres FK violation. `showStatus` timers clobber each other. `isAuthError` misclassifies RLS permission denials as session expiry.
- **Rating overwrite (#44):** Editing a session whose rating is NULL and changing only the notes silently persists `rating = 5` (`item.rating || 5` seeds the slider and the payload always includes it).
- **XSS posture — good.** `escapeHtml` is applied consistently at every sink handling user text, in both text and attribute contexts; textareas are set via `safeSetValue` post-render. Only some integer-typed interpolations (`sets`, `reps`, `rating`) skip escaping — defense-in-depth territory, not exploitable while those columns are numeric.

## Schema Findings (#46)

Verified against the live database:

1. **Client owns all timestamps.** `created_at` is NOT NULL with no DB default; `updated_at` depends on each client code path remembering to set it. With MCP now writing SQL directly against this database, DB defaults (`SET DEFAULT now()`) plus a `moddatetime` trigger make the data self-consistent regardless of writer.
2. **Natural-key FKs block renames.** `sessions.location → locations.name` and `training.exercise → exercises.name` with NO ACTION: renaming a gym or exercise is rejected while any row references it. Recreate both FKs with `ON UPDATE CASCADE` — keeps the readable names (genuinely nice for SQL/MCP analysis) while making renames a single UPDATE.
3. **No covering indexes** on `climbs.session_id`, `sessions.location`, `training.exercise` (performance advisor). Trivial at current row counts (109/57/169), free to fix.
4. **Identity vs. ordering.** The `S`/`C`/`T` + epoch-ms text PKs are fine as identity — do **not** migrate them. But the Edit tab sorts by PK (insertion order), so back-filled entries appear out of order and can push recent ones out of the 10-item window. Sort by `date desc` (sessions/training) and `created_at desc` (climbs) instead.

## Architecture Assessment (not filed as issues)

The single-file, no-build approach remains the right call at this scale — no framework warranted. The schema is fundamentally sound. Assumptions worth challenging:

- **Form duplication is the real drift risk.** Every entity's form exists twice in different technologies — create forms as static HTML, edit forms as JS template strings — with field lists repeated again in the submit and update handlers. Adding one field means touching four places; missing the edit path means every subsequent edit silently nulls that field. Proportionate fix: a small field-descriptor array per entity (`{col, elementId, kind}`) driving all four paths. ~200 lines saved, and create/edit become structurally incapable of diverging.
- **Data loading is fine at this scale** — with one honest exception: `loadSessions` fetches all sessions unbounded, and the edit-climb dropdown renders every one as an `<option>`. In two years that's a 300-entry dropdown on a phone. Add `.gte('date', <30 days ago>).limit(50)`.
- **Deploy-on-push with zero checks:** the proportionate answer is *do almost nothing* — at most a 5-line GitHub Action running `node --check` on the extracted script block. Full CI is overkill here. ✅ Done 2026-07-11 — `.github/workflows/syntax-check.yml` runs a line-number-preserving awk extraction + `node --check` on every push/PR; gate verified green and by sabotage test.
- **No backup path (#47)** is the single biggest long-term risk: free-tier Supabase projects pause after ~1 week of inactivity (an injury month is exactly this scenario), the app hard-deletes with no undo, and there's no point-in-time recovery. A monthly snapshot committed to this repo — via a scheduled Claude/MCP task or a cron GitHub Action — covers it and doubles as keep-alive.

### Deletion-pass cleanups

- ~~Unused `.quick-buttons` / `.quick-button` CSS (~25 dead lines).~~ ✅ Done 2026-07-11 — deleted.
- ~~`localStorage.setItem('lastLocation', ...)` — written, never read. Delete it or implement last-location pre-select (arguably the better call for a gym app).~~ ✅ Done 2026-07-11 — pre-select implemented at the end of `loadLocations()`, guarded by an `availableLocations.includes` check so a deactivated location falls back to the placeholder.
- ~~Redundant first clause in the 7-day session filter (`s.date >= today` is a strict subset of the 7-day condition).~~ ✅ Already resolved by `251179b` (single string-compare condition).
- ~~`rowToSession` maps 8 columns while `loadSessions` selects 3 — misleading to a future reader.~~ ✅ Done 2026-07-11 — dead `timestamp`/`lastUpdated` fields removed from all three mappers (client timestamps were dropped in #46); a comment above `rowToSession` now explains the narrow `loadSessions` select vs. the Edit tab's `select('*')`.
- ~~`currentRating`/`editRating` globals shadow the sliders' DOM values; reading the input at submit time removes a stale-state bug class.~~ ✅ Done 2026-07-11 — both globals removed; create path reads the slider at submit, edit path uses a `dataset.touched` flag on the (per-render) slider element to preserve the #44 null-until-touched semantics.
- ~~`insertRow` centralizes the auth-error/status pattern but `updateEntry` and `confirmDelete` re-inline the identical block — one shared helper covers all three.~~ ✅ Done 2026-07-11 — `performWrite(query, action, successMessage)` now wraps every insert/update/delete (error routing stays in `reportWriteError`, extracted earlier by `251179b`); `insertRow` deleted.
- Stray `data/nul` file (Windows reserved device name, reappeared 2026-01-27) — see #38.

## Suggested Order of Attack

1. ~~**#39** — ~10 minutes of dashboard toggles + five policy rewrites; closes the only real attack surface.~~ ✅ Done 2026-07-11.
2. **#41** — small code fix plus the data audit, before more rows skew.
3. **#40** — one-line fix in `loadEditData()`.
4. Batch the rest (#42–#47, #44, #38) into one afternoon; #46 is a single small migration.

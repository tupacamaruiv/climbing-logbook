"""One-time migration of GitHub JSON files into Supabase (architecture-plan.md, Step 4).

Reads credentials from .env.migration (git-ignored) or environment variables.
Uses only the Python standard library â€” no pip install required.
Inserts are upserts on the primary key, so the script is safe to rerun after
a partial failure without creating duplicates.

Run from the repo root:  python migrate.py
"""

import json
import os
import sys
import urllib.error
import urllib.request

EXPECTED = {'sessions': 108, 'climbs': 57, 'training': 169}


def load_credentials():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if (not url or not key) and os.path.exists('.env.migration'):
        with open('.env.migration') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                k, v = k.strip(), v.strip().strip('"\'')
                if k == 'SUPABASE_URL' and not url:
                    url = v
                elif k == 'SUPABASE_SERVICE_ROLE_KEY' and not key:
                    key = v
    if not url or not key or 'your-project' in url or key.startswith('paste-'):
        sys.exit('Credentials missing. Fill in SUPABASE_URL and '
                 'SUPABASE_SERVICE_ROLE_KEY in .env.migration first.')
    return url.rstrip('/'), key


SUPABASE_URL, SERVICE_ROLE_KEY = load_credentials()


def api(method, path, body=None, headers=None):
    """Returns (status_code, response_text, response_headers)."""
    req = urllib.request.Request(f'{SUPABASE_URL}/rest/v1/{path}', method=method)
    req.add_header('apikey', SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as res:
            return res.status, res.read().decode(), dict(res.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)


def clean(value):
    """Empty strings become None so they store as NULL."""
    return None if value == '' else value


def migrate(file, table, remap):
    with open(file, encoding='utf-8') as f:
        records = json.load(f)
    errors = []
    for r in records:
        payload = {}
        for col, key in remap.items():
            val = clean(r.get(key))
            if val is not None:
                payload[col] = val
        # merge-duplicates = upsert on the primary key, so reruns are safe
        status, text, _ = api('POST', table, payload,
                              {'Prefer': 'resolution=merge-duplicates'})
        if status >= 300:
            errors.append((r.get(list(remap.values())[0]), status, text))
    print(f'{table}: {len(records) - len(errors)} inserted, {len(errors)} errors '
          f'(expected {EXPECTED[table]})')
    for rec_id, status, text in errors:
        print(f'  ERROR {status} on {rec_id}: {text}')
    return len(errors)


def verify_count(table):
    _, _, headers = api('GET', f'{table}?select=*',
                        headers={'Prefer': 'count=exact', 'Range': '0-0'})
    content_range = headers.get('Content-Range', '?/?')
    actual = content_range.split('/')[-1]
    ok = actual == str(EXPECTED[table])
    print(f'  {table}: {actual} rows in Supabase '
          f'({"OK" if ok else "MISMATCH, expected " + str(EXPECTED[table])})')
    return ok


total_errors = 0

total_errors += migrate('data/archive/sessions.json', 'sessions', {
    'session_id':  'sessionId',
    'date':        'date',
    'location':    'location',
    'rating':      'rating',      # rpe intentionally dropped â€” rating is the kept field
    'notes':       'notes',
    'media':       'videos',      # renamed to media
    'created_at':  'timestamp',
    'updated_at':  'lastUpdated',
})

# sessions must exist before climbs (session_id foreign key)
total_errors += migrate('data/archive/climbs.json', 'climbs', {
    'climb_id':              'climbId',
    'session_id':            'sessionId',
    'boulder_name':          'boulderName',
    'grade':                 'grade',        # gradeSystem dropped â€” encoded in grade value
    'send_status':           'sendStatus',
    'is_project':            'isProject',
    'attempts':              'attempts',
    'performance_highlight': 'performanceHighlight',
    'notes':                 'notes',
    'media':                 'videos',       # renamed to media
    'created_at':            'timestamp',
    'updated_at':            'lastUpdated',
})

total_errors += migrate('data/archive/training.json', 'training', {
    'training_id':           'trainingId',
    'date':                  'date',
    'exercise':              'exercise',
    'sets':                  'sets',
    'reps':                  'reps',
    'weight':                'weight',
    'performance_highlight': 'performanceHighlight',
    'notes':                 'notes',
    'created_at':            'timestamp',
    'updated_at':            'lastUpdated',  # present on 4 records
})

print('\nVerifying row counts in Supabase:')
all_ok = all([verify_count('sessions'), verify_count('climbs'), verify_count('training')])

if total_errors == 0 and all_ok:
    print('\nMigration complete â€” all counts match.')
else:
    sys.exit('\nMigration finished with problems â€” review the errors above and rerun '
             '(reruns are safe, inserts are upserts).')

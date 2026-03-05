"""Full setup verification and migration runner."""
import subprocess
import sys
import os
import json

os.chdir('/Users/huya/Documents/Dev/SiWorkShop/backend')
sys.path.insert(0, '.')

VENV = '/Users/huya/Documents/Dev/SiWorkShop/backend/.venv/bin'
PG_BIN = '/opt/homebrew/opt/postgresql@16/bin'
NODE_BIN = '/opt/homebrew/opt/node@20/bin'
BREW_BIN = '/opt/homebrew/bin'

env = {**os.environ, 'PATH': f"{PG_BIN}:{NODE_BIN}:{BREW_BIN}:{os.environ.get('PATH', '')}"}

report = {}

# 1. Check PostgreSQL connectivity
r = subprocess.run([f'{PG_BIN}/psql', '-U', 'siuser', '-d', 'siworkgroup', '-c', 'SELECT version();'],
    capture_output=True, text=True, env=env)
report['pg_connect'] = 'OK' if r.returncode == 0 else f'FAIL: {r.stderr[:200]}'

# 2. Check tables
r = subprocess.run([f'{PG_BIN}/psql', '-U', 'siuser', '-d', 'siworkgroup', '-c', r'\dt'],
    capture_output=True, text=True, env=env)
report['tables'] = r.stdout.strip() or r.stderr.strip()

# 3. Check alembic current
r = subprocess.run([f'{VENV}/alembic', 'current'],
    capture_output=True, text=True, env=env,
    cwd='/Users/huya/Documents/Dev/SiWorkShop/backend')
report['alembic_current'] = r.stdout.strip() + r.stderr.strip()

# 4. Run alembic upgrade if needed
if 'head' not in report['alembic_current']:
    r = subprocess.run([f'{VENV}/alembic', 'upgrade', 'head'],
        capture_output=True, text=True, env=env,
        cwd='/Users/huya/Documents/Dev/SiWorkShop/backend')
    report['alembic_upgrade'] = r.stdout.strip() + r.stderr.strip()
    report['alembic_upgrade_exit'] = r.returncode
else:
    report['alembic_upgrade'] = 'already at head'

# 5. Check tables after upgrade
r = subprocess.run([f'{PG_BIN}/psql', '-U', 'siuser', '-d', 'siworkgroup', '-c', r'\dt'],
    capture_output=True, text=True, env=env)
report['tables_after'] = r.stdout.strip() or r.stderr.strip()

# 6. Redis check
r = subprocess.run([f'{BREW_BIN}/redis-cli', 'ping'], capture_output=True, text=True)
report['redis'] = r.stdout.strip()

# 7. Node/npm versions
r = subprocess.run([f'{NODE_BIN}/node', '--version'], capture_output=True, text=True)
report['node'] = r.stdout.strip() or r.stderr.strip()
r = subprocess.run([f'{NODE_BIN}/npm', '--version'], capture_output=True, text=True)
report['npm'] = r.stdout.strip() or r.stderr.strip()

# Write result
with open('/Users/huya/Documents/Dev/SiWorkShop/backend/full_setup_result.json', 'w') as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
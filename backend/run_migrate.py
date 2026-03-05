"""Script to run alembic migrations and check database state."""
import subprocess
import sys
import os

os.chdir('/Users/huya/Documents/Dev/SiWorkShop/backend')
sys.path.insert(0, '.')

pg_bin = '/opt/homebrew/opt/postgresql@16/bin'
env = {**os.environ, 'PATH': f"{pg_bin}:/opt/homebrew/bin:{os.environ.get('PATH', '')}"}

results = []

# Run alembic upgrade
r = subprocess.run(
    [sys.executable.replace('python3', 'alembic').replace('python', 'alembic')
     if False else '/Users/huya/Documents/Dev/SiWorkShop/backend/.venv/bin/alembic',
     'upgrade', 'head'],
    capture_output=True, text=True, env=env,
    cwd='/Users/huya/Documents/Dev/SiWorkShop/backend'
)
results.append('=== ALEMBIC UPGRADE ===')
results.append(f'stdout: {r.stdout}')
results.append(f'stderr: {r.stderr}')
results.append(f'exit: {r.returncode}')

# Check tables
r2 = subprocess.run(
    [f'{pg_bin}/psql', '-U', 'siuser', '-d', 'siworkgroup', '-c', r'\dt'],
    capture_output=True, text=True, env=env
)
results.append('=== DB TABLES ===')
results.append(r2.stdout or r2.stderr)

# Redis check
r3 = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
results.append('=== REDIS ===')
results.append(r3.stdout.strip())

output = '\n'.join(results)
with open('migrate_result.txt', 'w') as f:
    f.write(output)
print(output)
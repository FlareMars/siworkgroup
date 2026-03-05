#!/usr/bin/env python3
"""Remove next.config.ts and ensure next.config.mjs exists."""
import os
import json

FRONTEND = '/Users/huya/Documents/Dev/SiWorkShop/frontend'
TS_CONFIG = os.path.join(FRONTEND, 'next.config.ts')
MJS_CONFIG = os.path.join(FRONTEND, 'next.config.mjs')

result = {}

# Remove next.config.ts if it exists
if os.path.exists(TS_CONFIG):
    os.remove(TS_CONFIG)
    result['removed_ts'] = True
    print(f"✓ Removed {TS_CONFIG}")
else:
    result['removed_ts'] = False
    print(f"✓ {TS_CONFIG} already removed")

# Verify next.config.mjs exists
if os.path.exists(MJS_CONFIG):
    result['mjs_ok'] = True
    print(f"✓ {MJS_CONFIG} exists")
    print(f"  Content: {open(MJS_CONFIG).read()[:100]}")
else:
    # Create it
    mjs_content = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
'''
    with open(MJS_CONFIG, 'w') as f:
        f.write(mjs_content)
    result['mjs_ok'] = 'created'
    print(f"✓ Created {MJS_CONFIG}")

# List all next.config.* files
config_files = [f for f in os.listdir(FRONTEND) if f.startswith('next.config')]
result['config_files'] = config_files
print(f"Config files in frontend: {config_files}")

# Write result
with open('/Users/huya/Documents/Dev/SiWorkShop/backend/fix_result.json', 'w') as f:
    json.dump(result, f, indent=2)

print(json.dumps(result, indent=2))
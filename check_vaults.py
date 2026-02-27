import requests, json, sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from collections import Counter

url = 'https://stats-data.hyperliquid.xyz/Mainnet/vaults'
data = requests.get(url, timeout=60).json()

rel_types = Counter()
for v in data:
    s = v.get('summary', {})
    rel = s.get('relationship', {})
    if isinstance(rel, dict):
        rel_type = rel.get('type', 'none')
    else:
        rel_type = 'none'
    rel_types[rel_type] += 1

print('relationship 타입 분포:')
for k, cnt in rel_types.most_common():
    print(f'  {k!r}: {cnt}개')

# parent/child가 아닌 것 = User Vault
user_vaults = [v for v in data
    if v.get('summary', {}).get('relationship', {}) is None
    or (isinstance(v.get('summary', {}).get('relationship', {}), dict)
        and v.get('summary', {}).get('relationship', {}).get('type', '') not in ('parent', 'child'))]

print(f'\nUser Vault 후보: {len(user_vaults)}개')

with_tvl_uv = [v for v in user_vaults if float(v.get('summary', {}).get('tvl', 0) or 0) > 0]
print(f'TVL > 0인 User Vault: {len(with_tvl_uv)}개')

with_tvl_uv.sort(key=lambda x: float(x['summary'].get('tvl', 0)), reverse=True)
print('\n상위 5개:')
for v in with_tvl_uv[:5]:
    s = v['summary']
    print(f"  {s['name']} | TVL: {float(s.get('tvl',0)):,.0f} | rel: {s.get('relationship')}")

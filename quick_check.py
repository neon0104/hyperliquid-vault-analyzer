import json
data = json.load(open('vault_data/snapshots/2026-03-12.json', encoding='utf-8'))
print(f"총 {len(data)}개 볼트")
for v in data[:5]:
    print(f"  {v['rank']}. {v['name']} - APR:{v['apr_30d']}% Score:{v['score']}")

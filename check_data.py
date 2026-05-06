import json

with open(r'C:\Users\Administrator\lol\lol-assistant\data\augments.json', encoding='utf-8') as f:
    data = json.load(f)

champion_keys = list(data.get('data', {}).keys())
if champion_keys:
    champion = champion_keys[0]
    print('Champion:', champion)
    print('Sample augment entry:')
    print(json.dumps(data['data'][champion], indent=2, ensure_ascii=False)[:2000])
else:
    print('No data found')

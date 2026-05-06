import requests

url = 'https://lol-api-champion.op.gg/api/GLOBAL/champions/aram-mayhem/pantheon'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = requests.get(url, headers=headers, timeout=10)
print('Status:', resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print('Keys:', list(data.keys()) if isinstance(data, dict) else 'not dict')
    if 'data' in data:
        print('Data keys:', list(data['data'].keys())[:10])
        # Print full data structure
        import json
        print(json.dumps(data, indent=2)[:2000])
else:
    print('Response:', resp.text[:500])

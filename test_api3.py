import requests
import json

url = 'https://lol-api-champion.op.gg/api/GLOBAL/champions/arena/pantheon'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = requests.get(url, headers=headers, timeout=10)
print('Status:', resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    # Print all keys at top level
    print('Top keys:', list(data.keys()))
    # Print data structure
    if 'data' in data:
        inner_data = data['data']
        print('Inner data keys:', list(inner_data.keys()))
        # Check for augments
        for key in inner_data.keys():
            if 'augment' in key.lower():
                print(f'Found: {key}')
                print(json.dumps(inner_data[key], indent=2)[:1000])

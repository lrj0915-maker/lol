import requests

# Test different API endpoints
endpoints = [
    # Try arena first (we know this works)
    ('https://lol-api-champion.op.gg/api/GLOBAL/champions/arena/pantheon', 'arena'),
    # Try aram
    ('https://lol-api-champion.op.gg/api/GLOBAL/champions/aram/pantheon', 'aram'),
    # Try aram-mayhem variations
    ('https://lol-api-champion.op.gg/api/GLOBAL/champions/aram_mayhem/pantheon', 'aram_mayhem'),
    ('https://lol-api-champion.op.gg/api/GLOBAL/champions/aram-mayhem/pantheon', 'aram-mayhem'),
    ('https://lol-api-champion.op.gg/api/GLOBAL/champions/aramMayhem/pantheon', 'aramMayhem'),
    # Try without "champions" in path
    ('https://lol-api-champion.op.gg/api/GLOBAL/modes/aram-mayhem/pantheon', 'modes/aram-mayhem'),
    ('https://lol-api-champion.op.gg/api/GLOBAL/modes/aram/pantheon', 'modes/aram'),
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for url, name in endpoints:
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"{name}: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  -> Keys: {list(data.keys())}")
            if 'data' in data:
                print(f"  -> Data keys: {list(data['data'].keys())[:5]}")
    except Exception as e:
        print(f"{name}: Error - {e}")

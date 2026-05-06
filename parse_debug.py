import requests
import re
import json

# Fetch the page
url = 'https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers, timeout=30)
html = response.text

# Save HTML
with open('debug.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Saved HTML: {len(html)} chars')

# Find augment data
start = html.find('[{"id":')
if start >= 0:
    print(f'Found JSON at position {start}')
    
    # Find matching closing bracket
    depth = 0
    i = start
    while i < len(html):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                break
        i += 1
    
    json_str = html[start:i+1]
    
    try:
        data = json.loads(json_str)
        print(f'Parsed {len(data)} augments')
        print('\nFirst 3 augments:')
        for item in data[:3]:
            print(f"  ID: {item.get('id')}, Name: {item.get('name')}, Tier: {item.get('tier')}, Rarity: {item.get('rarity')}")
        
        # Show structure
        print('\nSample augment:')
        print(json.dumps(data[0], indent=2)[:1000])
    except Exception as e:
        print(f'Parse error: {e}')
        print('Sample:', json_str[:500])

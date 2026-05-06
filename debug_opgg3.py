import requests
import re
import json

url = 'https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

resp = requests.get(url, headers=headers, timeout=30)
print('Status:', resp.status_code)

if resp.status_code == 200:
    html = resp.text
    
    # Save full HTML for inspection
    with open('debug_full.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Saved to debug_full.html')
    print(f'HTML length: {len(html)}')
    
    # Print last 5000 characters
    print('\n--- Last 5000 chars ---')
    print(html[-5000:])

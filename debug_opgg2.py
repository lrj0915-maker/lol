import requests
import re
import json

url = 'https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

resp = requests.get(url, headers=headers, timeout=30)
print('Status:', resp.status_code)

if resp.status_code == 200:
    html = resp.text
    
    # Try different patterns
    patterns = [
        r'window\.__NEXT_DATA__\s*=\s*(\{.*?\});',
        r'pageProps\s*=\s*(\{.*?\});',
        r'"augments"\s*:\s*\[',
        r'"augment_group"\s*:\s*\[',
    ]
    
    for pattern in patterns:
        matches = list(re.finditer(pattern, html))
        print(f'Pattern "{pattern[:30]}...": {len(matches)} matches')
        
    # Look for data-* attributes that might contain JSON
    if 'augment' in html.lower():
        # Find where augments are mentioned
        idx = html.lower().find('augment')
        print(f'First mention at: {idx}')
        print(f'Context: {html[idx:idx+200]}')

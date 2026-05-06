import requests
import re
import json

url = 'https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

resp = requests.get(url, headers=headers, timeout=30)
print('Status:', resp.status_code)

if resp.status_code == 200:
    html = resp.text
    
    # Look for __NEXT_DATA__
    match = re.search(r'window\.__NEXT_DATA__\s*=\s*(\{.*?\});', html, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            print('Found __NEXT_DATA__')
            print('Keys:', list(data.keys()))
            
            # Navigate to props -> pageProps
            props = data.get('props', {})
            print('Props keys:', list(props.keys()))
            
            page_props = props.get('pageProps', {})
            print('PageProps keys:', list(page_props.keys()))
            
            # Save for inspection
            with open('debug_opgg.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print('Saved to debug_opgg.json')
        except Exception as e:
            print(f'Parse error: {e}')

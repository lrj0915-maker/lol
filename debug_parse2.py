import re
import json
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
resp = requests.get(url, headers=HEADERS, timeout=30)
html = resp.text

# Find all "data" arrays in the HTML
# The pattern is "data":[{"id":...

pattern = r'"data":\[\{"id":'
matches = list(re.finditer(pattern, html))

print(f"Found {len(matches)} matches for 'data:[{{id'")

if matches:
    # Look at the first match
    m = matches[0]
    start = m.start()
    print(f"First at {start}")
    
    # Find the array - look for matching brackets
    # First find the opening [
    arr_start = html.find('[', start + len('"data":'))
    if arr_start >= 0:
        # Count brackets to find the end
        depth = 0
        i = arr_start
        while i < len(html):
            if html[i] == '[':
                depth += 1
            elif html[i] == ']':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        
        json_str = html[arr_start:i+1]
        print(f"JSON length: {len(json_str)}")
        print(f"First 200 chars: {json_str[:200]}")
        
        # Try to parse
        try:
            data = json.loads(json_str)
            print(f"Parsed {len(data)} items")
            for item in data[:3]:
                print(f"  {item.get('name')}: tier={item.get('tier')}, perf={item.get('performance')}, pop={item.get('popular')}")
        except Exception as e:
            print(f"Error: {e}")

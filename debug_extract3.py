import re
import json
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
resp = requests.get(url, headers=HEADERS, timeout=30)
html = resp.text

# Find the script with data
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)

for i, script in enumerate(scripts):
    if '"data":[{' in script:
        print(f"Script {i}")
        
        # Find all JSON arrays in this script
        # The data we want starts with "data\":[{\"id\":"
        start = script.find('data')
        if start >= 0:
            # Find the full JSON - it may be escaped
            # Try a different approach - find the actual data array
            # Look for "data:[" pattern
            match = re.search(r'"data"\s*:\s*(\[.*?\])', script)
            if match:
                print(f"  Match: {match.group(1)[:100]}...")

import re
import json
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
resp = requests.get(url, headers=HEADERS, timeout=30)
html = resp.text

# Find the script tag that contains the JSON data
# It's probably in a self.__next_f.push call
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)

print(f"Found {len(scripts)} script tags")

# Look for ones containing augment data
for i, script in enumerate(scripts):
    if 'id' in script and 'name' in script and len(script) > 1000:
        # Check if it has augment-like data
        if 'Executioner' in script or 'id' in script:
            print(f"\nScript {i}: {len(script)} chars")
            # Show sample
            print(script[:500])
            # Try to extract JSON
            if '[' in script:
                start = script.find('[')
                print(f"  Starts with: {script[start:start+100]}")

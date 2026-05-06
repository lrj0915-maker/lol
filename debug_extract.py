import re
import json
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
resp = requests.get(url, headers=HEADERS, timeout=30)
html = resp.text

# Find the script with "5b:" which contains the augment data
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)

for i, script in enumerate(scripts):
    if '"data":[{' in script and '"id":' in script and '"name":' in script:
        print(f"Found in script {i}")
        
        # Extract the JSON data
        match = re.search(r'"data":(\[.*?\])', script, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                print(f"  Parsed {len(data)} augments")
                
                # Show first few
                for aug in data[:3]:
                    print(f"    {aug.get('name')}: tier={aug.get('tier')}, perf={aug.get('performance')}, pop={aug.get('popular')}")
            except Exception as e:
                print(f"  Error: {e}")

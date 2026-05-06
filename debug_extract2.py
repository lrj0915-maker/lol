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
        
        # Try to extract and parse more carefully
        # Look for the data array
        start = script.find('"data":[')
        if start >= 0:
            # Find the matching ]
            bracket_start = script.find('[', start)
            depth = 0
            j = bracket_start
            while j < len(script):
                if script[j] == '[':
                    depth += 1
                elif script[j] == ']':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            
            json_str = script[bracket_start:j+1]
            print(f"  JSON at {bracket_start} to {j}, length {len(json_str)}")
            
            try:
                data = json.loads(json_str)
                print(f"  Parsed {len(data)} augments")
                
                # Show first few
                for aug in data[:5]:
                    print(f"    {aug.get('name')}: tier={aug.get('tier')}, perf={aug.get('performance')}, pop={aug.get('popular')}")
            except Exception as e:
                print(f"  Error: {e}")
                print(f"  Sample: {json_str[:200]}")

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
    print(html[start:start+500])

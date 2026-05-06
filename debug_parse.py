import re
import json
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
resp = requests.get(url, headers=HEADERS, timeout=30)
html = resp.text

# Try to find the JSON data
print("Searching for JSON patterns...")
patterns = [
    r'\[\{"id":\d+',
    r'"augments":\s*\[',
    r'"Performance":\s*\d+',
    r'"performance":\s*\d+',
]

for p in patterns:
    matches = re.findall(p, html, re.IGNORECASE)
    print(f"  {p}: {len(matches)} matches")

# Look at specific parts of the HTML
print("\nLooking for 'Executioner'...")
if "Executioner" in html:
    idx = html.find("Executioner")
    print(f"  Found at {idx}")
    print(f"  Context: {html[idx:idx+200]}")

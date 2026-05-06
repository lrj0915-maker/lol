"""Test script to verify ARAM: Mayhem data fetching works."""

import sys
sys.path.insert(0, 'scripts')

from pathlib import Path
import json
import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Test fetch and parse
url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
response = requests.get(url, headers=HEADERS, timeout=30)
html = response.text
print(f"Fetched: {len(html)} chars")

# Parse augments
start = html.find('[{"id":')
if start >= 0:
    # Find matching closing bracket
    depth = 0
    i = start
    while i < len(html):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                break
        i += 1
    
    json_str = html[start:i+1]
    data = json.loads(json_str)
    print(f"Found {len(data)} augments")
    
    # Show first few
    print("\nFirst 5 augments:")
    for aug in data[:5]:
        print(f"  ID: {aug.get('id')}, Name: {aug.get('name')}, Tier: {aug.get('tier')}, Rarity: {aug.get('rarity')}, Performance: {aug.get('performance')}, Popular: {aug.get('popular')}")

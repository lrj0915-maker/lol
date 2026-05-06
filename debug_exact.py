import re
import json
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
resp = requests.get(url, headers=HEADERS, timeout=30)
html = resp.text

# Find the exact pattern we saw in debug_scripts.py
# It was: self.__next_f.push([1,"5b:["$","$L5c",null,{"data":[{"id":...

# Search for this pattern
idx = html.find('5b:["$","$L5c"')
if idx >= 0:
    print(f"Found at {idx}")
    
    # Get a chunk of HTML around this
    chunk = html[idx:idx+2000]
    print(chunk[:1000])

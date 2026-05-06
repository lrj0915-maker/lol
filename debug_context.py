import re
import json
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = "https://www.op.gg/lol/modes/aram-mayhem/pantheon/augments"
resp = requests.get(url, headers=HEADERS, timeout=30)
html = resp.text

# Look around position 273811 for Executioner
idx = html.find("Executioner")
start = max(0, idx - 500)
end = min(len(html), idx + 1000)

print("Context around Executioner:")
print(html[start:end])

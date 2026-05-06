import requests
import re

resp = requests.get('https://www.op.gg/modes/arena/katarina/augments', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

# 找强化图标 URL
# 格式: src="https://opgg-static.akamaized.net/meta/images/lol/latest/augment/marksmage_large.png
pattern = r'augment/(\w+)_large\.png'
icons = re.findall(pattern, text)
print(f"Found {len(icons)} augment icons:")
for icon in icons[:20]:
    print(f"  {icon}")
    print(f"  URL: https://opgg-static.akamaized.net/meta/images/lol/latest/augment/{icon}_large.png")

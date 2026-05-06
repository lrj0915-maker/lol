import requests
import re

resp = requests.get('https://www.op.gg/modes/arena/katarina/augments', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

# 找到每个强化块，提取名称和图标
# 每个强化块的结构：<img src="...augment/xxx_large.png"...><strong>名称</strong>
block_pattern = r'augment/(\w+)_large\.png[^>]*>.*?<strong class="ml-2 truncate text-gray-900">([^<]+)</strong>'
matches = re.findall(block_pattern, text, re.DOTALL)

print(f'Found {len(matches)} augment blocks')
for i, (icon, name) in enumerate(matches[:15]):
    name = name.replace('&#x27;', "'").replace('&amp;', '&')
    print(f'{i+1}. {name} - icon: {icon}')

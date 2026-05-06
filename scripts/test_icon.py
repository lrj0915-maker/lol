import requests
import re

resp = requests.get('https://www.op.gg/modes/arena/katarina/augments', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

# 先提取所有图标 key
icon_pattern = r'augment/(\w+)_large\.png'
icons = re.findall(icon_pattern, text)
print(f'Found {len(icons)} icons')

# 匹配强化名称
pattern = r'<strong class="ml-2 truncate text-gray-900">([^<]+)</strong>.*?<span class="font-bold">(\d+\.?\d*)%</span>'
matches = re.findall(pattern, text)
print(f'Found {len(matches)} augments')

# 显示前10个
for i, match in enumerate(matches[:10]):
    icon_idx = i * 4
    icon = icons[icon_idx] if icon_idx < len(icons) else 'N/A'
    print(f'{i+1}. {match[0]} - {match[1]}% - icon: {icon}')

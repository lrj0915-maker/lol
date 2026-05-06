"""测试爬取装备推荐数据 - 更精确的解析"""
import requests
import re

resp = requests.get('https://www.op.gg/modes/arena/yasuo/build', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

# 查找装备块：图片 + 名称 + 选取率
# 模式: <img src="...item/ID.png"...>...<strong>名称</strong>...<span>XX%</span>
pattern = r'item/(\d+)\.png[^>]*>.*?<strong class="[^"]*">([^<]+)</strong>.*?<span class="font-bold">(\d+\.?\d*)%</span>'
matches = re.findall(pattern, text, re.DOTALL)

print(f"找到 {len(matches)} 个装备:")
for item_id, name, rate in matches[:15]:
    name = name.replace('&#x27;', "'").strip()
    print(f"  {item_id}: {name} - {rate}%")

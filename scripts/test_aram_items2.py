"""测试爬取 ARAM 装备推荐数据 - 分析HTML结构"""
import requests
import re

resp = requests.get('https://www.op.gg/modes/aram/yasuo/build', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

# 保存HTML分析
with open('aram_build.html', 'w', encoding='utf-8') as f:
    f.write(text)

# 查找包含装备的区块
# 找 "Core Build" 或类似的区域
core_match = re.search(r'Core Build.*?</section>', text, re.DOTALL | re.IGNORECASE)
if core_match:
    print("找到 Core Build 区域")
    core_text = core_match.group()
    items = re.findall(r'item/(\d+)\.png', core_text)
    print(f"核心装备: {items}")

# 尝试另一种模式 - 找装备图片和选取率
# <img...item/ID.png...>...<span...>XX%</span>
pattern = r'<img[^>]*item/(\d+)\.png[^>]*>.*?(\d+\.?\d*)%'
matches = re.findall(pattern, text, re.DOTALL)
print(f"\n找到 {len(matches)} 个装备+选取率:")
seen = set()
for item_id, rate in matches:
    if item_id not in seen and float(rate) > 1:
        seen.add(item_id)
        print(f"  装备 {item_id}: {rate}%")

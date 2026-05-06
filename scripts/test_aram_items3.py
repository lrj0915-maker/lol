"""测试爬取 ARAM 装备推荐数据 - 完整解析"""
import requests
import re

resp = requests.get('https://www.op.gg/modes/aram/yasuo/build', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

# 1. 核心装备 - 找 Core Build 区域的前3个装备
core_match = re.search(r'Core Build.*?(?=Boots|Skill|$)', text, re.DOTALL | re.IGNORECASE)
if core_match:
    core_text = core_match.group()[:2000]  # 只取前2000字符
    core_items = re.findall(r'item/(\d+)\.png', core_text)
    # 去重但保持顺序
    seen = set()
    unique_core = []
    for item in core_items:
        if item not in seen:
            seen.add(item)
            unique_core.append(item)
    print(f"核心装备 (前3): {unique_core[:3]}")

# 2. 鞋子 - 找 Boots 区域
boots_match = re.search(r'Boots.*?(?=Skill|Starter|$)', text, re.DOTALL | re.IGNORECASE)
if boots_match:
    boots_text = boots_match.group()[:1500]
    boots_items = re.findall(r'item/(\d+)\.png', boots_text)
    seen = set()
    unique_boots = []
    for item in boots_items:
        if item not in seen:
            seen.add(item)
            unique_boots.append(item)
    print(f"鞋子选择: {unique_boots[:3]}")

# 3. 起始装备
starter_match = re.search(r'Starter.*?(?=Core|Skill|$)', text, re.DOTALL | re.IGNORECASE)
if starter_match:
    starter_text = starter_match.group()[:1500]
    starter_items = re.findall(r'item/(\d+)\.png', starter_text)
    seen = set()
    unique_starter = []
    for item in starter_items:
        if item not in seen:
            seen.add(item)
            unique_starter.append(item)
    print(f"起始装备: {unique_starter[:3]}")

print("\n装备图标URL示例:")
print(f"https://opgg-static.akamaized.net/meta/images/lol/latest/item/3153.png")

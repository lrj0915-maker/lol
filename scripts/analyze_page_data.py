"""分析页面中的所有强化数据"""
import re

with open('opgg_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("=== 分析页面中的强化数据 ===\n")

# 1. 查找所有强化图标出现的位置和上下文
augment_pattern = r'augment/(\w+)_large\.png'
matches = list(re.finditer(augment_pattern, html))

print(f"找到 {len(matches)} 个强化图标引用\n")

# 分析每个位置
positions = {}
for m in matches:
    icon = m.group(1)
    pos = m.start()
    
    if icon not in positions:
        positions[icon] = []
    positions[icon].append(pos)

print(f"不同强化数量: {len(positions)}\n")

# 检查每个强化出现的位置
print("=== 强化出现位置分析 ===")
for icon, pos_list in list(positions.items())[:10]:
    print(f"\n{icon}: 出现 {len(pos_list)} 次")
    for pos in pos_list[:2]:
        # 获取上下文
        context_before = html[max(0, pos-200):pos]
        context_after = html[pos:pos+300]
        
        # 检查是否在表格中
        in_table = '<td>' in context_before or '<tr>' in context_before
        # 检查是否有选取率数据
        has_rate = re.search(r'(\d+\.?\d*)%', context_after)
        
        print(f"  位置 {pos}: 表格={in_table}, 有选取率={bool(has_rate)}")
        if has_rate:
            print(f"    选取率: {has_rate.group(1)}%")

# 2. 检查是否有 Synergies 区域的数据
print("\n\n=== Synergies 区域分析 ===")
synergies_match = re.search(r'Synergies.*?(?=Augments|Items|Skills|$)', html, re.DOTALL | re.IGNORECASE)
if synergies_match:
    synergies_text = synergies_match.group()[:3000]
    synergies_augments = re.findall(r'augment/(\w+)_large\.png', synergies_text)
    print(f"Synergies 区域强化: {synergies_augments}")

# 3. 检查是否有隐藏的数据区块
print("\n\n=== 检查隐藏数据 ===")
# 查找 display:none 或 hidden 的区块
hidden_sections = re.findall(r'(display:\s*none|hidden)[^>]*>.*?augment/(\w+)_large\.png', html, re.DOTALL)
print(f"隐藏区块中的强化: {len(hidden_sections)}")

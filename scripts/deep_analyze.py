"""深入分析 HTML 结构"""
import re

with open('opgg_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 查找所有强化图标和对应的数据
print("=== 分析强化数据结构 ===")

# 方法1: 查找所有 augment 图标出现的位置
augment_positions = []
for m in re.finditer(r'augment/(\w+)_large\.png', html):
    pos = m.start()
    icon = m.group(1)
    # 获取周围的上下文
    context = html[pos:pos+500]
    augment_positions.append((icon, pos, context))

print(f"找到 {len(augment_positions)} 个强化图标位置")

# 分析每个位置的上下文，看是否有 tier 信息
for icon, pos, context in augment_positions[:5]:
    print(f"\n图标: {icon}")
    # 查找名称
    name_match = re.search(r'<strong[^>]*>([^<]+)</strong>', context)
    if name_match:
        print(f"  名称: {name_match.group(1)}")
    # 查找百分比
    pct_match = re.search(r'(\d+\.?\d*)%', context)
    if pct_match:
        print(f"  选取率: {pct_match.group(1)}%")
    # 查找 tier 相关
    if 'silver' in context.lower():
        print("  包含 silver")
    if 'gold' in context.lower():
        print("  包含 gold")
    if 'prismatic' in context.lower():
        print("  包含 prismatic")

# 方法2: 查找页面中的 JSON 数据
print("\n\n=== 查找嵌入的数据 ===")

# 查找 script 标签
scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
print(f"找到 {len(scripts)} 个 script 标签")

for i, script in enumerate(scripts):
    if len(script) > 5000 and ('augment' in script.lower() or 'arena' in script.lower()):
        print(f"\nScript {i}: 长度 {len(script)}")
        # 保存这个 script 供分析
        with open(f'script_{i}.txt', 'w', encoding='utf-8') as f:
            f.write(script)
        print(f"  已保存到 script_{i}.txt")
        
        # 查找 tier 相关内容
        tier_matches = re.findall(r'.{0,50}(silver|gold|prismatic).{0,50}', script, re.IGNORECASE)
        if tier_matches:
            print(f"  tier 相关内容: {tier_matches[:3]}")

"""查找强化数据结构"""
import re
import json

with open('opgg_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("=== 搜索强化数据 ===")

# 1. 查找 augments 数组
augments_matches = list(re.finditer(r'"augments"\s*:\s*\[', html))
print(f"找到 {len(augments_matches)} 个 augments 数组")

for i, m in enumerate(augments_matches[:3]):
    pos = m.start()
    # 提取数组内容
    bracket_count = 0
    start = pos + len(m.group()) - 1
    end = start
    for j, c in enumerate(html[start:start+5000]):
        if c == '[':
            bracket_count += 1
        elif c == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end = start + j + 1
                break
    
    array_str = html[start:end]
    print(f"\n--- augments 数组 {i+1} (位置 {pos}) ---")
    print(f"长度: {len(array_str)}")
    print(f"内容预览: {array_str[:500]}...")

# 2. 查找包含 tier 的强化数据
print("\n\n=== 搜索 tier 数据 ===")
tier_patterns = [
    r'"tier"\s*:\s*"[^"]+"',
    r'"augmentTier"\s*:\s*"[^"]+"',
    r'"rarity"\s*:\s*"[^"]+"',
]

for pattern in tier_patterns:
    matches = re.findall(pattern, html)
    if matches:
        print(f"模式 {pattern}: {set(matches)}")

# 3. 查找强化名称和相关数据
print("\n\n=== 分析强化数据结构 ===")
# 查找 Marksmage 周围的数据
marksmage_pos = html.find('Marksmage')
if marksmage_pos > 0:
    context = html[marksmage_pos-500:marksmage_pos+500]
    print(f"Marksmage 上下文:")
    print(context)

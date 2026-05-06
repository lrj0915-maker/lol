"""检查页面中是否有所有等级的强化数据"""
import re

with open('opgg_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 提取所有强化图标
icons = re.findall(r'augment/(\w+)_large\.png', html)
unique_icons = list(dict.fromkeys(icons))  # 保持顺序去重

print(f"找到 {len(unique_icons)} 个不同的强化图标")
print("\n所有强化:")
for i, icon in enumerate(unique_icons):
    print(f"  {i+1}. {icon}")

# 检查这些强化的等级（根据 augments.js 中的数据）
silver_augments = [
    "witchfulthinking", "adapt", "goredrink", "infernalsoul", "spintowin",
    "bluntforce", "deft", "executioner", "legday", "typhoon"
]

gold_augments = [
    "marksmage", "itskillingtime", "threadtheneedle", "outlawsgrit",
    "magicmissile", "phenomenalevil", "bigbrain", "combomaster",
    "vulnerability", "frombeginningtoend", "apexinventor", "vanish",
    "bodyguard", "statsonstats"
]

prismatic_augments = [
    "transmuteprismatic", "acceleratingsorcery", "chainlightning",
    "jeweledgauntlet", "ultimaterevolution"
]

print("\n\n=== 等级分析 ===")
found_silver = [a for a in unique_icons if a in silver_augments]
found_gold = [a for a in unique_icons if a in gold_augments]
found_prismatic = [a for a in unique_icons if a in prismatic_augments]

print(f"银色强化: {len(found_silver)} - {found_silver}")
print(f"金色强化: {len(found_gold)} - {found_gold}")
print(f"棱彩强化: {len(found_prismatic)} - {found_prismatic}")

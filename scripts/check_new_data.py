"""检查新数据结构"""
import json

with open('data/augments.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('版本:', data.get('version'))
print('更新时间:', data.get('updateTime'))
print('英雄数量:', len(data.get('data', {})))

# 查看一个英雄的数据结构
if data.get('data'):
    champ_id = list(data['data'].keys())[0]
    champ = data['data'][champ_id]
    print(f'\n示例英雄 ({champ_id} - {champ.get("key")}):')
    augs = champ.get('augments', {})
    
    if isinstance(augs, dict):
        print('  强化 (新格式 - 按等级分类):')
        for tier in ['silver', 'gold', 'prismatic']:
            tier_augs = augs.get(tier, [])
            print(f'    {tier}: {len(tier_augs)} 个')
            if tier_augs:
                print(f'      示例: {tier_augs[0]}')
    elif isinstance(augs, list):
        print(f'  强化 (旧格式): {len(augs)} 个')
        if augs:
            print(f'    示例: {augs[0]}')

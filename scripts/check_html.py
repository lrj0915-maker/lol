"""检查 HTML 中的强化数据"""
import re

with open('opgg_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 查找所有强化名称
names = re.findall(r'<strong[^>]*class="[^"]*truncate[^"]*"[^>]*>([^<]+)</strong>', html)
print(f'找到 {len(names)} 个强化名称')
for i, name in enumerate(names[:30]):
    print(f'  {i+1}. {name}')

# 检查是否有 hidden 或 display:none 的区块
hidden_blocks = re.findall(r'hidden|display:\s*none', html)
print(f'\n隐藏元素数量: {len(hidden_blocks)}')

# 查找数据区块
# op.gg 可能用 React/Next.js，数据可能在 props 中
props_data = re.search(r'pageProps.*?augments', html)
if props_data:
    print(f'\n找到 pageProps 中的 augments')

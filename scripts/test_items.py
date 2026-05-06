"""测试爬取装备推荐数据"""
import requests
import re

resp = requests.get('https://www.op.gg/modes/arena/yasuo/build', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

# 保存 HTML 用于分析
with open('test_items.html', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"HTML 长度: {len(text)}")

# 查找装备图片 URL 模式
item_pattern = r'item/(\d+)\.png'
items = re.findall(item_pattern, text)
print(f"\n找到 {len(items)} 个装备ID:")
for item_id in list(set(items))[:20]:
    print(f"  {item_id}")

# 查找装备选取率
rate_pattern = r'item/(\d+)\.png.*?(\d+\.?\d*)%'
rates = re.findall(rate_pattern, text, re.DOTALL)
print(f"\n找到 {len(rates)} 个装备选取率:")
for item_id, rate in rates[:10]:
    print(f"  装备 {item_id}: {rate}%")

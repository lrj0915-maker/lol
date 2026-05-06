"""测试爬取 ARAM 装备推荐数据"""
import requests
import re

# ARAM 模式的装备页面
resp = requests.get('https://www.op.gg/modes/aram/yasuo/build', 
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
text = resp.text

print(f"HTML 长度: {len(text)}")

# 查找装备块
# 模式: item/ID.png...名称...选取率
pattern = r'item/(\d+)\.png[^>]*>.*?<strong[^>]*>([^<]+)</strong>.*?<span class="font-bold">(\d+\.?\d*)%</span>'
matches = re.findall(pattern, text, re.DOTALL)

print(f"\n找到 {len(matches)} 个装备:")
for item_id, name, rate in matches[:15]:
    name = name.replace('&#x27;', "'").strip()
    print(f"  {item_id}: {name} - {rate}%")

# 也查找鞋子
print("\n--- 查找所有装备图片 ---")
item_imgs = re.findall(r'item/(\d+)\.png', text)
print(f"找到 {len(item_imgs)} 个装备图片")
unique_items = list(set(item_imgs))
print(f"唯一装备: {len(unique_items)} 个")
for item_id in unique_items[:20]:
    print(f"  {item_id}")

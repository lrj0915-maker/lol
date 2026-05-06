"""查找 op.gg 的 API 端点"""
import re

with open('opgg_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 查找所有可能的 API URL
patterns = [
    r'https?://[^"\s<>]+api[^"\s<>]*',
    r'/api/[^"\s<>]+',
    r'_next/data/[^"\s<>]+',
]

print("=== 查找 API 端点 ===")
for pattern in patterns:
    matches = set(re.findall(pattern, html))
    if matches:
        print(f"\n模式: {pattern}")
        for m in list(matches)[:10]:
            print(f"  {m}")

# 查找 fetch 或 axios 调用
print("\n=== 查找数据加载逻辑 ===")
fetch_calls = re.findall(r'fetch\s*\(\s*["\']([^"\']+)["\']', html)
if fetch_calls:
    print(f"fetch 调用: {fetch_calls[:10]}")

# 查找 Next.js 数据
print("\n=== 查找 Next.js 数据 ===")
next_data = re.search(r'self\.__next_f\.push\(\[1,"([^"]+)"\]\)', html)
if next_data:
    data = next_data.group(1)[:500]
    print(f"Next.js 数据片段: {data}")

# 查找 buildId
build_id = re.search(r'"buildId"\s*:\s*"([^"]+)"', html)
if build_id:
    print(f"\nbuildId: {build_id.group(1)}")

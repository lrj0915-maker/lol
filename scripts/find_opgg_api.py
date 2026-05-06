"""尝试找到 op.gg 的 API"""
import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# 尝试不同的 API 端点
apis = [
    "https://www.op.gg/api/v1.0/internal/bypass/modes/arena/katarina/augments",
    "https://www.op.gg/api/modes/arena/katarina/augments",
    "https://lol-api-champion.op.gg/api/KR/champions/ranked/katarina",
    "https://lol-api-champion.op.gg/api/KR/champions/arena/katarina",
]

for api in apis:
    print(f"\n尝试: {api}")
    try:
        resp = requests.get(api, headers=HEADERS, timeout=10)
        print(f"  状态: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"  JSON 数据: {str(data)[:500]}")
            except:
                print(f"  非 JSON: {resp.text[:200]}")
    except Exception as e:
        print(f"  错误: {e}")

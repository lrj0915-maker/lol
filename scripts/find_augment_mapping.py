"""查找强化 ID 到名称的映射"""
import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# 尝试不同的 API 端点
apis = [
    "https://lol-api-champion.op.gg/api/KR/meta/arena/augments",
    "https://lol-api-champion.op.gg/api/KR/augments",
    "https://www.op.gg/api/augments",
    "https://lol-api-champion.op.gg/api/KR/meta/augments",
]

for api in apis:
    print(f"\n尝试: {api}")
    try:
        resp = requests.get(api, headers=HEADERS, timeout=10)
        print(f"  状态: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"  JSON 数据: {str(data)[:1000]}")
                # 保存
                filename = api.split('/')[-1] + '.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  已保存到 {filename}")
            except:
                print(f"  非 JSON: {resp.text[:200]}")
    except Exception as e:
        print(f"  错误: {e}")

# 也尝试从 Data Dragon 获取
print("\n\n=== 尝试 Data Dragon ===")
dd_apis = [
    "https://ddragon.leagueoflegends.com/cdn/14.24.1/data/en_US/augments.json",
    "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/arena-augments.json",
]

for api in dd_apis:
    print(f"\n尝试: {api}")
    try:
        resp = requests.get(api, headers=HEADERS, timeout=10)
        print(f"  状态: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"  JSON 数据: {str(data)[:1000]}")
                filename = 'dd_' + api.split('/')[-1]
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  已保存到 {filename}")
            except:
                print(f"  非 JSON: {resp.text[:200]}")
    except Exception as e:
        print(f"  错误: {e}")

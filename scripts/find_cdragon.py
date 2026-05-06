"""从 Community Dragon 获取强化数据"""
import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# Community Dragon 路径
apis = [
    "https://raw.communitydragon.org/latest/cdragon/arena/en_us.json",
    "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/cherry-augments.json",
    "https://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/default/v1/cherry-augments.json",
]

for api in apis:
    print(f"\n尝试: {api}")
    try:
        resp = requests.get(api, headers=HEADERS, timeout=15)
        print(f"  状态: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  数据类型: {type(data)}")
            if isinstance(data, list):
                print(f"  数组长度: {len(data)}")
                if data:
                    print(f"  第一个元素: {data[0]}")
            elif isinstance(data, dict):
                print(f"  键: {list(data.keys())[:10]}")
            
            # 保存
            filename = 'cdragon_' + api.split('/')[-1]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  已保存到 {filename}")
    except Exception as e:
        print(f"  错误: {e}")

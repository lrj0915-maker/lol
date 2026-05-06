"""测试 OP.GG API 返回的完整数据结构"""
import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def test_api():
    url = "https://lol-api-champion.op.gg/api/KR/champions/arena/katarina"
    
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        
        # 保存完整响应
        with open("opgg_api_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("✓ 完整响应已保存到 opgg_api_response.json")
        
        # 打印数据结构
        if 'data' in data:
            print("\n数据结构:")
            for key in data['data'].keys():
                value = data['data'][key]
                if isinstance(value, list):
                    print(f"  {key}: list[{len(value)}]")
                    if value and isinstance(value[0], dict):
                        print(f"    keys: {list(value[0].keys())}")
                elif isinstance(value, dict):
                    print(f"  {key}: dict")
                    print(f"    keys: {list(value.keys())}")
                else:
                    print(f"  {key}: {type(value).__name__}")
    else:
        print(f"✗ 请求失败: {resp.status_code}")

if __name__ == "__main__":
    test_api()

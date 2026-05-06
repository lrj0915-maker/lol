"""测试不同 tier 的 URL"""
import requests
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# 尝试不同的 URL 格式
urls = [
    "https://www.op.gg/modes/arena/katarina/augments",
    "https://www.op.gg/modes/arena/katarina/augments?tier=silver",
    "https://www.op.gg/modes/arena/katarina/augments?tier=gold", 
    "https://www.op.gg/modes/arena/katarina/augments?tier=prismatic",
    "https://www.op.gg/modes/arena/katarina/augments?augmentTier=silver",
    "https://www.op.gg/modes/arena/katarina/augments/silver",
]

for url in urls:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        # 提取强化名称
        names = re.findall(r'<strong[^>]*class="[^"]*truncate[^"]*"[^>]*>([^<]+)</strong>', resp.text)
        
        # 检查哪个按钮是激活的
        silver_active = 'bg-main-500' in resp.text.split('Silver')[0][-200:] if 'Silver' in resp.text else False
        gold_active = 'bg-main-500' in resp.text.split('Gold')[0][-200:] if 'Gold' in resp.text else False
        
        print(f"\n{url}")
        print(f"  强化数量: {len(names)}")
        print(f"  前5个: {names[:5]}")
        
    except Exception as e:
        print(f"\n{url}")
        print(f"  错误: {e}")

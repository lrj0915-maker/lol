"""
测试 op.gg 强化等级数据获取
"""
import requests
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def fetch_with_retry(url, max_retries=3):
    """带重试的请求"""
    for i in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            return resp.text
        except Exception as e:
            print(f"  重试 {i+1}/{max_retries}: {e}")
            time.sleep(2)
    return None

def analyze_augment_structure(html):
    """分析强化数据结构"""
    # 查找所有强化块
    # 每个强化有: 图标、名称、选取率、场次
    
    # 方法1: 查找 augment 图标模式
    augment_icons = re.findall(r'augment/(\w+)_large\.png', html)
    print(f"找到 {len(augment_icons)} 个强化图标")
    print(f"前10个: {augment_icons[:10]}")
    
    # 方法2: 查找包含 tier 信息的 JSON 或 HTML
    # op.gg 可能在 __NEXT_DATA__ 中存储数据
    next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if next_data:
        json_str = next_data.group(1)
        print(f"\n找到 __NEXT_DATA__, 长度: {len(json_str)}")
        
        # 查找 tier 相关内容
        if 'silver' in json_str.lower():
            print("  包含 silver 数据")
        if 'gold' in json_str.lower():
            print("  包含 gold 数据")
        if 'prismatic' in json_str.lower():
            print("  包含 prismatic 数据")
        
        # 提取一小段看结构
        tier_match = re.search(r'"tier"\s*:\s*"(\w+)"', json_str)
        if tier_match:
            print(f"  tier 格式示例: {tier_match.group()}")
        
        # 保存完整 JSON 供分析
        with open('augment_data_sample.json', 'w', encoding='utf-8') as f:
            f.write(json_str)
        print("  已保存到 augment_data_sample.json")
    
    # 方法3: 查找 HTML 中的 tier 标记
    tier_patterns = [
        r'tier["\s:=]+["\']?(silver|gold|prismatic)',
        r'(silver|gold|prismatic)["\s]*tier',
        r'class="[^"]*(?:silver|gold|prismatic)[^"]*"',
    ]
    for pattern in tier_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"\n模式 '{pattern}' 找到: {matches[:5]}")

def main():
    print("=== 测试 op.gg 强化等级数据 ===\n")
    
    url = "https://www.op.gg/modes/arena/katarina/augments"
    print(f"获取: {url}")
    
    html = fetch_with_retry(url)
    if not html:
        print("获取失败!")
        return
    
    print(f"页面长度: {len(html)}\n")
    analyze_augment_structure(html)

if __name__ == "__main__":
    main()

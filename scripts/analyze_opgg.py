"""
分析 op.gg 页面结构，找出如何获取不同等级的强化数据
"""
import requests
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def main():
    url = "https://www.op.gg/modes/arena/katarina/augments"
    print(f"获取: {url}")
    
    resp = requests.get(url, headers=HEADERS, timeout=15)
    html = resp.text
    print(f"页面长度: {len(html)}")
    
    # 保存 HTML 供分析
    with open('opgg_sample.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("已保存 HTML 到 opgg_sample.html")
    
    # 查找强化图标
    icons = re.findall(r'augment/(\w+)_large\.png', html)
    print(f"\n找到 {len(icons)} 个强化图标")
    print(f"前20个: {icons[:20]}")
    
    # 查找 tier 相关内容
    print("\n=== Tier 分析 ===")
    
    # 在 HTML 中搜索 silver/gold/prismatic 周围的内容
    for tier in ['Silver', 'Gold', 'Prismatic']:
        idx = html.find(f'>{tier}<')
        if idx > 0:
            context = html[idx-200:idx+200]
            print(f"\n{tier} 上下文:")
            print(context[:300])

if __name__ == "__main__":
    main()

"""
从 OP.GG 网页爬取符文推荐数据
使用 BeautifulSoup 解析 HTML
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

# 英雄列表（简化版，用于测试）
TEST_CHAMPIONS = [
    {"id": 157, "key": "yasuo", "name": "亚索"},
    {"id": 238, "key": "zed", "name": "劫"},
    {"id": 55, "key": "katarina", "name": "卡特琳娜"},
]

# 位置映射
POSITIONS = {
    "top": "上单",
    "jungle": "打野", 
    "mid": "中单",
    "adc": "ADC",
    "support": "辅助"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def fetch_champion_page(champion_key, position):
    """获取英雄页面HTML"""
    url = f"https://www.op.gg/champions/{champion_key}/build/{position}"
    
    try:
        print(f"  访问: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            print(f"  ✓ 成功获取页面 ({len(resp.text)} 字节)")
            return resp.text
        else:
            print(f"  ✗ 失败: HTTP {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"  ✗ 异常: {e}")
        return None

def parse_runes_from_html(html):
    """从HTML中解析符文数据"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 保存HTML用于调试
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  已保存HTML到 debug_page.html")
    
    # 查找符文相关的元素
    # OP.GG 使用 CSS 类名来标识符文区域
    rune_sections = soup.find_all(class_=lambda x: x and 'rune' in x.lower())
    
    print(f"  找到 {len(rune_sections)} 个符文相关元素")
    
    # 查找所有可能包含数据的 script 标签
    scripts = soup.find_all('script')
    print(f"  找到 {len(scripts)} 个 script 标签")
    
    # 尝试从 script 标签中提取 JSON 数据
    for i, script in enumerate(scripts):
        if script.string and ('rune' in script.string.lower() or 'perk' in script.string.lower()):
            print(f"  Script {i} 可能包含符文数据:")
            print(f"    {script.string[:200]}...")
            
            # 保存可能包含数据的 script
            with open(f"debug_script_{i}.txt", "w", encoding="utf-8") as f:
                f.write(script.string)
    
    # 查找 Next.js 的数据
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data and next_data.string:
        print(f"  ✓ 找到 __NEXT_DATA__")
        try:
            data = json.loads(next_data.string)
            with open("debug_next_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  已保存 Next.js 数据到 debug_next_data.json")
            return data
        except:
            print(f"  ✗ 解析 __NEXT_DATA__ 失败")
    
    return None

def test_single_champion():
    """测试单个英雄"""
    champion = TEST_CHAMPIONS[0]  # 亚索
    position = "mid"
    
    print(f"\n{'='*60}")
    print(f"测试: {champion['name']} ({champion['key']}) - {POSITIONS[position]}")
    print(f"{'='*60}\n")
    
    html = fetch_champion_page(champion['key'], position)
    
    if html:
        data = parse_runes_from_html(html)
        
        if data:
            print(f"\n✓ 成功解析数据!")
            print(f"  数据结构: {list(data.keys())[:10]}")
            return True
        else:
            print(f"\n✗ 未能解析出符文数据")
            print(f"\n提示: 请查看生成的调试文件:")
            print(f"  - debug_page.html (完整页面)")
            print(f"  - debug_next_data.json (Next.js数据)")
            print(f"  - debug_script_*.txt (可能包含数据的脚本)")
    
    return False

def main():
    print("=" * 60)
    print("OP.GG 符文数据爬取 - HTML解析版本")
    print("=" * 60)
    
    success = test_single_champion()
    
    if success:
        print("\n\n下一步: 分析 debug_next_data.json 找到符文数据的位置")
        print("然后编写解析函数提取符文、装备、召唤师技能等数据")
    else:
        print("\n\n请检查调试文件，找到数据所在位置")

if __name__ == "__main__":
    main()

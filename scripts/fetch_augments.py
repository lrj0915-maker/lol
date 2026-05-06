"""
从 op.gg 爬取所有英雄的 Arena 强化推荐数据
"""
import requests
import json
import time
import re
from pathlib import Path

# 英雄列表（从 champions.js 提取）
CHAMPIONS = [
    {"id": 266, "key": "Aatrox"},
    {"id": 103, "key": "Ahri"},
    {"id": 84, "key": "Akali"},
    {"id": 166, "key": "Akshan"},
    {"id": 12, "key": "Alistar"},
    {"id": 799, "key": "Ambessa"},
    {"id": 32, "key": "Amumu"},
    {"id": 34, "key": "Anivia"},
    {"id": 1, "key": "Annie"},
    {"id": 523, "key": "Aphelios"},
    {"id": 22, "key": "Ashe"},
    {"id": 136, "key": "AurelionSol"},
    {"id": 893, "key": "Aurora"},
    {"id": 268, "key": "Azir"},
    {"id": 432, "key": "Bard"},
    {"id": 200, "key": "Belveth"},
    {"id": 53, "key": "Blitzcrank"},
    {"id": 63, "key": "Brand"},
    {"id": 201, "key": "Braum"},
    {"id": 233, "key": "Briar"},
    {"id": 51, "key": "Caitlyn"},
    {"id": 164, "key": "Camille"},
    {"id": 69, "key": "Cassiopeia"},
    {"id": 31, "key": "Chogath"},
    {"id": 42, "key": "Corki"},
    {"id": 122, "key": "Darius"},
    {"id": 131, "key": "Diana"},
    {"id": 119, "key": "Draven"},
    {"id": 36, "key": "DrMundo"},
    {"id": 245, "key": "Ekko"},
    {"id": 60, "key": "Elise"},
    {"id": 28, "key": "Evelynn"},
    {"id": 81, "key": "Ezreal"},
    {"id": 9, "key": "Fiddlesticks"},
    {"id": 114, "key": "Fiora"},
    {"id": 105, "key": "Fizz"},
    {"id": 3, "key": "Galio"},
    {"id": 41, "key": "Gangplank"},
    {"id": 86, "key": "Garen"},
    {"id": 150, "key": "Gnar"},
    {"id": 79, "key": "Gragas"},
    {"id": 104, "key": "Graves"},
    {"id": 887, "key": "Gwen"},
    {"id": 120, "key": "Hecarim"},
    {"id": 74, "key": "Heimerdinger"},
    {"id": 910, "key": "Hwei"},
    {"id": 420, "key": "Illaoi"},
    {"id": 39, "key": "Irelia"},
    {"id": 427, "key": "Ivern"},
    {"id": 40, "key": "Janna"},
    {"id": 59, "key": "JarvanIV"},
    {"id": 24, "key": "Jax"},
    {"id": 126, "key": "Jayce"},
    {"id": 202, "key": "Jhin"},
    {"id": 222, "key": "Jinx"},
    {"id": 145, "key": "Kaisa"},
    {"id": 429, "key": "Kalista"},
    {"id": 43, "key": "Karma"},
    {"id": 30, "key": "Karthus"},
    {"id": 38, "key": "Kassadin"},
    {"id": 55, "key": "Katarina"},
    {"id": 10, "key": "Kayle"},
    {"id": 141, "key": "Kayn"},
    {"id": 85, "key": "Kennen"},
    {"id": 121, "key": "Khazix"},
    {"id": 203, "key": "Kindred"},
    {"id": 240, "key": "Kled"},
    {"id": 96, "key": "KogMaw"},
    {"id": 897, "key": "KSante"},
    {"id": 7, "key": "Leblanc"},
    {"id": 64, "key": "LeeSin"},
    {"id": 89, "key": "Leona"},
    {"id": 876, "key": "Lillia"},
    {"id": 127, "key": "Lissandra"},
    {"id": 236, "key": "Lucian"},
    {"id": 117, "key": "Lulu"},
    {"id": 99, "key": "Lux"},
    {"id": 54, "key": "Malphite"},
    {"id": 90, "key": "Malzahar"},
    {"id": 57, "key": "Maokai"},
    {"id": 11, "key": "MasterYi"},
    {"id": 800, "key": "Mel"},
    {"id": 902, "key": "Milio"},
    {"id": 21, "key": "MissFortune"},
    {"id": 62, "key": "MonkeyKing"},
    {"id": 82, "key": "Mordekaiser"},
    {"id": 25, "key": "Morgana"},
    {"id": 950, "key": "Naafiri"},
    {"id": 267, "key": "Nami"},
    {"id": 75, "key": "Nasus"},
    {"id": 111, "key": "Nautilus"},
    {"id": 518, "key": "Neeko"},
    {"id": 76, "key": "Nidalee"},
    {"id": 895, "key": "Nilah"},
    {"id": 56, "key": "Nocturne"},
    {"id": 20, "key": "Nunu"},
    {"id": 2, "key": "Olaf"},
    {"id": 61, "key": "Orianna"},
    {"id": 516, "key": "Ornn"},
    {"id": 80, "key": "Pantheon"},
    {"id": 78, "key": "Poppy"},
    {"id": 555, "key": "Pyke"},
    {"id": 246, "key": "Qiyana"},
    {"id": 133, "key": "Quinn"},
    {"id": 497, "key": "Rakan"},
    {"id": 33, "key": "Rammus"},
    {"id": 421, "key": "RekSai"},
    {"id": 526, "key": "Rell"},
    {"id": 888, "key": "Renata"},
    {"id": 58, "key": "Renekton"},
    {"id": 107, "key": "Rengar"},
    {"id": 92, "key": "Riven"},
    {"id": 68, "key": "Rumble"},
    {"id": 13, "key": "Ryze"},
    {"id": 360, "key": "Samira"},
    {"id": 113, "key": "Sejuani"},
    {"id": 235, "key": "Senna"},
    {"id": 147, "key": "Seraphine"},
    {"id": 875, "key": "Sett"},
    {"id": 35, "key": "Shaco"},
    {"id": 98, "key": "Shen"},
    {"id": 102, "key": "Shyvana"},
    {"id": 27, "key": "Singed"},
    {"id": 14, "key": "Sion"},
    {"id": 15, "key": "Sivir"},
    {"id": 72, "key": "Skarner"},
    {"id": 901, "key": "Smolder"},
    {"id": 37, "key": "Sona"},
    {"id": 16, "key": "Soraka"},
    {"id": 50, "key": "Swain"},
    {"id": 517, "key": "Sylas"},
    {"id": 134, "key": "Syndra"},
    {"id": 223, "key": "TahmKench"},
    {"id": 163, "key": "Taliyah"},
    {"id": 91, "key": "Talon"},
    {"id": 44, "key": "Taric"},
    {"id": 17, "key": "Teemo"},
    {"id": 412, "key": "Thresh"},
    {"id": 18, "key": "Tristana"},
    {"id": 48, "key": "Trundle"},
    {"id": 23, "key": "Tryndamere"},
    {"id": 4, "key": "TwistedFate"},
    {"id": 29, "key": "Twitch"},
    {"id": 77, "key": "Udyr"},
    {"id": 6, "key": "Urgot"},
    {"id": 110, "key": "Varus"},
    {"id": 67, "key": "Vayne"},
    {"id": 45, "key": "Veigar"},
    {"id": 161, "key": "Velkoz"},
    {"id": 711, "key": "Vex"},
    {"id": 254, "key": "Vi"},
    {"id": 234, "key": "Viego"},
    {"id": 112, "key": "Viktor"},
    {"id": 8, "key": "Vladimir"},
    {"id": 106, "key": "Volibear"},
    {"id": 19, "key": "Warwick"},
    {"id": 498, "key": "Xayah"},
    {"id": 101, "key": "Xerath"},
    {"id": 5, "key": "XinZhao"},
    {"id": 157, "key": "Yasuo"},
    {"id": 777, "key": "Yone"},
    {"id": 83, "key": "Yorick"},
    {"id": 804, "key": "Yunara"},
    {"id": 350, "key": "Yuumi"},
    {"id": 904, "key": "Zaahen"},
    {"id": 154, "key": "Zac"},
    {"id": 238, "key": "Zed"},
    {"id": 221, "key": "Zeri"},
    {"id": 115, "key": "Ziggs"},
    {"id": 26, "key": "Zilean"},
    {"id": 142, "key": "Zoe"},
    {"id": 143, "key": "Zyra"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def parse_augments(html_text):
    """解析强化数据，包含图标 key"""
    augments = []
    
    # 找到每个强化块，提取图标和名称
    # 每个强化块的结构：<img src="...augment/xxx_large.png"...><strong>名称</strong>...<span>百分比%</span><span>场次</span>
    block_pattern = r'augment/(\w+)_large\.png[^>]*>.*?<strong class="ml-2 truncate text-gray-900">([^<]+)</strong>.*?<span class="font-bold">(\d+\.?\d*)%</span><span class="text-gray-500">(\d+(?:,\d+)*)'
    matches = re.findall(block_pattern, html_text, re.DOTALL)
    
    for match in matches:
        icon_key = match[0]
        name = match[1].strip()
        # 处理 HTML 实体
        name = name.replace('&#x27;', "'")
        name = name.replace('&amp;', '&')
        pick_rate = float(match[2])
        games = int(match[3].replace(',', ''))
        
        if name and pick_rate > 0:
            augments.append({
                "name": name,
                "icon": icon_key,
                "pickRate": pick_rate,
                "games": games
            })
    
    return augments  # 返回所有强化数据

def parse_items(html_text):
    """解析 ARAM 装备数据"""
    items = {
        "core": [],
        "boots": [],
        "starter": []
    }
    
    # 1. 核心装备 - 找 Core Build 区域
    core_match = re.search(r'Core Build.*?(?=Boots|Skill|$)', html_text, re.DOTALL | re.IGNORECASE)
    if core_match:
        core_text = core_match.group()[:2000]
        core_items = re.findall(r'item/(\d+)\.png', core_text)
        seen = set()
        for item in core_items:
            if item not in seen:
                seen.add(item)
                items["core"].append(item)
                if len(items["core"]) >= 3:
                    break
    
    # 2. 鞋子
    boots_match = re.search(r'Boots.*?(?=Skill|Starter|Core|$)', html_text, re.DOTALL | re.IGNORECASE)
    if boots_match:
        boots_text = boots_match.group()[:1500]
        boots_items = re.findall(r'item/(\d+)\.png', boots_text)
        seen = set()
        for item in boots_items:
            if item not in seen:
                seen.add(item)
                items["boots"].append(item)
                if len(items["boots"]) >= 2:
                    break
    
    # 3. 起始装备
    starter_match = re.search(r'Starter.*?(?=Core|Skill|Boots|$)', html_text, re.DOTALL | re.IGNORECASE)
    if starter_match:
        starter_text = starter_match.group()[:1500]
        starter_items = re.findall(r'item/(\d+)\.png', starter_text)
        seen = set()
        for item in starter_items:
            if item not in seen:
                seen.add(item)
                items["starter"].append(item)
                if len(items["starter"]) >= 2:
                    break
    
    return items

def fetch_champion_augments(champion_key):
    """获取单个英雄的强化数据"""
    url_key = champion_key.lower()
    url = f"https://www.op.gg/modes/arena/{url_key}/augments"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return parse_augments(resp.text)
        else:
            print(f"  HTTP {resp.status_code}")
            return []
    except Exception as e:
        print(f"  Error: {e}")
        return []

def fetch_champion_items(champion_key):
    """获取单个英雄的 ARAM 装备数据"""
    url_key = champion_key.lower()
    url = f"https://www.op.gg/modes/aram/{url_key}/build"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return parse_items(resp.text)
        else:
            return {"core": [], "boots": [], "starter": []}
    except Exception as e:
        return {"core": [], "boots": [], "starter": []}

def test_single_champion():
    """测试单个英雄，确保能获取数据"""
    print("=== 测试单个英雄 (Katarina) ===")
    augments = fetch_champion_augments("Katarina")
    items = fetch_champion_items("Katarina")
    
    if augments:
        print(f"✓ 成功获取 {len(augments)} 个强化:")
        for i, aug in enumerate(augments[:5]):
            print(f"  {i+1}. {aug['name']} - {aug['pickRate']}%")
    else:
        print("✗ 强化获取失败!")
        return False
    
    if items["core"]:
        print(f"✓ 成功获取装备:")
        print(f"  核心: {items['core']}")
        print(f"  鞋子: {items['boots']}")
        print(f"  起始: {items['starter']}")
    else:
        print("✗ 装备获取失败!")
    
    return True

def main():
    # 先测试单个英雄
    print("步骤1: 测试单个英雄...")
    if not test_single_champion():
        print("\n测试失败，请检查网络或解析逻辑!")
        return
    
    print("\n步骤2: 开始爬取所有英雄...")
    print(f"共 {len(CHAMPIONS)} 个英雄\n")
    
    result = {
        "version": "16.01",
        "updateTime": time.strftime("%Y-%m-%d"),
        "data": {}
    }
    
    success_count = 0
    fail_count = 0
    failed_champions = []
    
    for i, champ in enumerate(CHAMPIONS):
        champ_id = str(champ["id"])
        champ_key = champ["key"]
        
        print(f"[{i+1}/{len(CHAMPIONS)}] {champ_key}...", end=" ", flush=True)
        
        augments = fetch_champion_augments(champ_key)
        items = fetch_champion_items(champ_key)
        
        if augments:
            result["data"][champ_id] = {
                "key": champ_key.lower(),
                "augments": augments,
                "items": items
            }
            print(f"✓ {len(augments)} 强化, {len(items['core'])} 核心装备")
            success_count += 1
        else:
            print("✗ 无数据")
            fail_count += 1
            failed_champions.append(champ_key)
        
        # 控制请求频率，避免被封
        time.sleep(1.0)
    
    # 保存结果
    output_path = Path(__file__).parent.parent / "data" / "augments.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！")
    print(f"成功: {success_count}, 失败: {fail_count}")
    print(f"数据已保存到: {output_path}")
    
    if failed_champions:
        print(f"\n失败的英雄: {', '.join(failed_champions)}")

if __name__ == "__main__":
    main()

"""
从 op.gg 爬取所有英雄的 Arena 强化推荐数据 (v2)
支持获取所有等级 (Silver, Gold, Prismatic) 的强化
"""
import requests
import json
import time
import re
from pathlib import Path

# 从 augments.js 导入的强化等级数据
AUGMENT_TIERS = {
    # Silver
    "404 Augment Not Found": "silver", "ADAPt": "silver", "Augmented Power": "silver",
    "Blunt Force": "silver", "Bravest of the Brave": "silver", "Buff Buddies": "silver",
    "Calculated Risk": "silver", "Cannon Fodder": "silver", "Castle": "silver",
    "Clothesline": "silver", "Contract Killer": "silver", "Deft": "silver",
    "Dematerialize": "silver", "Desecrator": "silver", "Dive Bomber": "silver",
    "Don't Blink": "silver", "Don't Chase": "silver", "Erosion": "silver",
    "EscAPADe": "silver", "Executioner": "silver", "Fallen Aegis": "silver",
    "Firefox": "silver", "Fire Sale": "silver", "First-Aid Kit": "silver",
    "Flashbang": "silver", "Frost Wraith": "silver", "Frozen Foundations": "silver",
    "Fruits of Your Labor": "silver", "Goredrink": "silver", "Guilty Pleasure": "silver",
    "Heavy Hitter": "silver", "Hold Very Still": "silver", "Homeguard": "silver",
    "Ice Cold": "silver", "Infernal Soul": "silver", "Juice Box": "silver",
    "Juice Press": "silver", "Leg Day": "silver", "Light 'em Up": "silver",
    "Mind to Matter": "silver", "Mirror Image": "silver", "Mountain Soul": "silver",
    "Now You See Me": "silver", "Numb to Pain": "silver", "Ocean Soul": "silver",
    "Parasitic Mutation": "silver", "Repulsor": "silver", "Scoped Weapons": "silver",
    "Self Destruct": "silver", "Serve Beyond Death": "silver", "Shadow Runner": "silver",
    "Slap Around": "silver", "Slime Time": "silver", "Snowball Fight!": "silver",
    "Sonic Boom": "silver", "Spin To Win": "silver", "Spirit Infusion": "silver",
    "Stackosaurus Rex": "silver", "Stats!": "silver", "Tank It Or Leave It": "silver",
    "Tormentor": "silver", "Trailblazer": "silver", "Transmute: Gold": "silver",
    "Typhoon": "silver", "Ultimate Unstoppable": "silver", "Warmup Routine": "silver",
    "Witchful Thinking": "silver",
    
    # Gold
    "All For You": "gold", "And My Axe!": "gold", "Apex Inventor": "gold",
    "Banner of Command": "gold", "Big Brain": "gold", "Blood Brother": "gold",
    "Bodyguard": "gold", "Bread And Butter": "gold", "Bread And Cheese": "gold",
    "Bread And Jam": "gold", "Celestial Body": "gold", "Combo Master": "gold",
    "Critical Healing": "gold", "Dark Blessing": "gold", "Dawnbringer's Resolve": "gold",
    "Deathtouch": "gold", "Defensive Maneuvers": "gold", "Demon's Dance": "gold",
    "Die Another Day": "gold", "Divine Intervention": "gold", "Ethereal Weapon": "gold",
    "Extendo-Arm": "gold", "Firebrand": "gold", "Flashy": "gold",
    "From Beginning to End": "gold", "Hat Trick": "gold", "Holy Fire": "gold",
    "Impassable": "gold", "It's Critical": "gold", "It's Killing Time": "gold",
    "Keystone Conjurer": "gold", "Light Warden": "gold", "Lightning Strikes": "gold",
    "Magic Missile": "gold", "Marksmage": "gold", "Minionmancer": "gold",
    "OK Boomerang": "gold", "Oathsworn": "gold", "Outlaw's Grit": "gold",
    "Overflow": "gold", "Parasitic Relationship": "gold", "Perseverance": "gold",
    "Phenomenal Evil": "gold", "Quest: Angel of Retribution": "gold",
    "Quest: Mad Hatter": "gold", "Quest: Steel Your Heart": "gold",
    "Quest: Three Sacred Treasures": "gold", "Quest: Urf's Champion": "gold",
    "Rabble Rousing": "gold", "Recursion": "gold", "Restart": "gold",
    "Restless Restoration": "gold", "Scopier Weapons": "gold", "Searing Dawn": "gold",
    "Shrink Ray": "gold", "Skilled Sniper": "gold", "Slow and Steady": "gold",
    "Soul Siphon": "gold", "Stats on Stats!": "gold", "Summoner Revolution": "gold",
    "Symbiotic Mutation": "gold", "Tank Engine": "gold", "The Brutalizer": "gold",
    "Thread the Needle": "gold", "Transmute: Prismatic": "gold", "Trickster Demon": "gold",
    "Twice Thrice": "gold", "Undying Guard": "gold", "Vanish": "gold",
    "Vengeance": "gold", "Vulnerability": "gold", "We'll Be Right Back": "gold",
    "Willing Sacrifice": "gold", "With Haste": "gold",
    
    # Prismatic
    "Accelerating Sorcery": "prismatic", "Augment 405": "prismatic",
    "Back to Basics": "prismatic", "Blade Waltz": "prismatic",
    "Can't Touch This": "prismatic", "Center of the Universe": "prismatic",
    "Cerberus": "prismatic", "Chain Lightning": "prismatic", "Chauffeur": "prismatic",
    "Circle of Death": "prismatic", "Clown College": "prismatic",
    "Courage of the Colossus": "prismatic", "Dashing": "prismatic",
    "Doomsayer": "prismatic", "Draw Your Sword": "prismatic",
    "Dreadbringer": "prismatic", "Dual Wield": "prismatic", "Earthwake": "prismatic",
    "Eureka": "prismatic", "Fan the Hammer": "prismatic", "Feel the Burn": "prismatic",
    "Fey Magic": "prismatic", "Gamba Anvil": "prismatic", "Giant Slayer": "prismatic",
    "Goliath": "prismatic", "Infernal Conduit": "prismatic",
    "Jeweled Gauntlet": "prismatic", "Laser Eyes": "prismatic",
    "Mad Scientist": "prismatic", "Master of Duality": "prismatic",
    "Mystic Punch": "prismatic", "Nesting Doll": "prismatic", "Null": "prismatic",
    "Omni Soul": "prismatic", "Orbital Laser": "prismatic",
    "Pandora's Box": "prismatic", "Prismatic Egg": "prismatic",
    "Quantum Computing": "prismatic", "Quest: Wooglet's Witchcap": "prismatic",
    "Raid Boss": "prismatic", "Scopiest Weapons": "prismatic",
    "Slow Cooker": "prismatic", "Spellwake": "prismatic", "Spirit Link": "prismatic",
    "Stats on Stats on Stats!": "prismatic", "Summoner's Roulette": "prismatic",
    "Symphony of War": "prismatic", "Tap Dancer": "prismatic",
    "Transmute: Chaos": "prismatic", "Trueshot Prodigy": "prismatic",
    "Ultimate Revolution": "prismatic", "Ultimate Roulette": "prismatic",
    "Wisdom of Ages": "prismatic",
}

# 英雄列表
CHAMPIONS = [
    {"id": 266, "key": "Aatrox"}, {"id": 103, "key": "Ahri"}, {"id": 84, "key": "Akali"},
    {"id": 166, "key": "Akshan"}, {"id": 12, "key": "Alistar"}, {"id": 799, "key": "Ambessa"},
    {"id": 32, "key": "Amumu"}, {"id": 34, "key": "Anivia"}, {"id": 1, "key": "Annie"},
    {"id": 523, "key": "Aphelios"}, {"id": 22, "key": "Ashe"}, {"id": 136, "key": "AurelionSol"},
    {"id": 893, "key": "Aurora"}, {"id": 268, "key": "Azir"}, {"id": 432, "key": "Bard"},
    {"id": 200, "key": "Belveth"}, {"id": 53, "key": "Blitzcrank"}, {"id": 63, "key": "Brand"},
    {"id": 201, "key": "Braum"}, {"id": 233, "key": "Briar"}, {"id": 51, "key": "Caitlyn"},
    {"id": 164, "key": "Camille"}, {"id": 69, "key": "Cassiopeia"}, {"id": 31, "key": "Chogath"},
    {"id": 42, "key": "Corki"}, {"id": 122, "key": "Darius"}, {"id": 131, "key": "Diana"},
    {"id": 119, "key": "Draven"}, {"id": 36, "key": "DrMundo"}, {"id": 245, "key": "Ekko"},
    {"id": 60, "key": "Elise"}, {"id": 28, "key": "Evelynn"}, {"id": 81, "key": "Ezreal"},
    {"id": 9, "key": "Fiddlesticks"}, {"id": 114, "key": "Fiora"}, {"id": 105, "key": "Fizz"},
    {"id": 3, "key": "Galio"}, {"id": 41, "key": "Gangplank"}, {"id": 86, "key": "Garen"},
    {"id": 150, "key": "Gnar"}, {"id": 79, "key": "Gragas"}, {"id": 104, "key": "Graves"},
    {"id": 887, "key": "Gwen"}, {"id": 120, "key": "Hecarim"}, {"id": 74, "key": "Heimerdinger"},
    {"id": 910, "key": "Hwei"}, {"id": 420, "key": "Illaoi"}, {"id": 39, "key": "Irelia"},
    {"id": 427, "key": "Ivern"}, {"id": 40, "key": "Janna"}, {"id": 59, "key": "JarvanIV"},
    {"id": 24, "key": "Jax"}, {"id": 126, "key": "Jayce"}, {"id": 202, "key": "Jhin"},
    {"id": 222, "key": "Jinx"}, {"id": 145, "key": "Kaisa"}, {"id": 429, "key": "Kalista"},
    {"id": 43, "key": "Karma"}, {"id": 30, "key": "Karthus"}, {"id": 38, "key": "Kassadin"},
    {"id": 55, "key": "Katarina"}, {"id": 10, "key": "Kayle"}, {"id": 141, "key": "Kayn"},
    {"id": 85, "key": "Kennen"}, {"id": 121, "key": "Khazix"}, {"id": 203, "key": "Kindred"},
    {"id": 240, "key": "Kled"}, {"id": 96, "key": "KogMaw"}, {"id": 897, "key": "KSante"},
    {"id": 7, "key": "Leblanc"}, {"id": 64, "key": "LeeSin"}, {"id": 89, "key": "Leona"},
    {"id": 876, "key": "Lillia"}, {"id": 127, "key": "Lissandra"}, {"id": 236, "key": "Lucian"},
    {"id": 117, "key": "Lulu"}, {"id": 99, "key": "Lux"}, {"id": 54, "key": "Malphite"},
    {"id": 90, "key": "Malzahar"}, {"id": 57, "key": "Maokai"}, {"id": 11, "key": "MasterYi"},
    {"id": 800, "key": "Mel"}, {"id": 902, "key": "Milio"}, {"id": 21, "key": "MissFortune"},
    {"id": 62, "key": "MonkeyKing"}, {"id": 82, "key": "Mordekaiser"}, {"id": 25, "key": "Morgana"},
    {"id": 950, "key": "Naafiri"}, {"id": 267, "key": "Nami"}, {"id": 75, "key": "Nasus"},
    {"id": 111, "key": "Nautilus"}, {"id": 518, "key": "Neeko"}, {"id": 76, "key": "Nidalee"},
    {"id": 895, "key": "Nilah"}, {"id": 56, "key": "Nocturne"}, {"id": 20, "key": "Nunu"},
    {"id": 2, "key": "Olaf"}, {"id": 61, "key": "Orianna"}, {"id": 516, "key": "Ornn"},
    {"id": 80, "key": "Pantheon"}, {"id": 78, "key": "Poppy"}, {"id": 555, "key": "Pyke"},
    {"id": 246, "key": "Qiyana"}, {"id": 133, "key": "Quinn"}, {"id": 497, "key": "Rakan"},
    {"id": 33, "key": "Rammus"}, {"id": 421, "key": "RekSai"}, {"id": 526, "key": "Rell"},
    {"id": 888, "key": "Renata"}, {"id": 58, "key": "Renekton"}, {"id": 107, "key": "Rengar"},
    {"id": 92, "key": "Riven"}, {"id": 68, "key": "Rumble"}, {"id": 13, "key": "Ryze"},
    {"id": 360, "key": "Samira"}, {"id": 113, "key": "Sejuani"}, {"id": 235, "key": "Senna"},
    {"id": 147, "key": "Seraphine"}, {"id": 875, "key": "Sett"}, {"id": 35, "key": "Shaco"},
    {"id": 98, "key": "Shen"}, {"id": 102, "key": "Shyvana"}, {"id": 27, "key": "Singed"},
    {"id": 14, "key": "Sion"}, {"id": 15, "key": "Sivir"}, {"id": 72, "key": "Skarner"},
    {"id": 901, "key": "Smolder"}, {"id": 37, "key": "Sona"}, {"id": 16, "key": "Soraka"},
    {"id": 50, "key": "Swain"}, {"id": 517, "key": "Sylas"}, {"id": 134, "key": "Syndra"},
    {"id": 223, "key": "TahmKench"}, {"id": 163, "key": "Taliyah"}, {"id": 91, "key": "Talon"},
    {"id": 44, "key": "Taric"}, {"id": 17, "key": "Teemo"}, {"id": 412, "key": "Thresh"},
    {"id": 18, "key": "Tristana"}, {"id": 48, "key": "Trundle"}, {"id": 23, "key": "Tryndamere"},
    {"id": 4, "key": "TwistedFate"}, {"id": 29, "key": "Twitch"}, {"id": 77, "key": "Udyr"},
    {"id": 6, "key": "Urgot"}, {"id": 110, "key": "Varus"}, {"id": 67, "key": "Vayne"},
    {"id": 45, "key": "Veigar"}, {"id": 161, "key": "Velkoz"}, {"id": 711, "key": "Vex"},
    {"id": 254, "key": "Vi"}, {"id": 234, "key": "Viego"}, {"id": 112, "key": "Viktor"},
    {"id": 8, "key": "Vladimir"}, {"id": 106, "key": "Volibear"}, {"id": 19, "key": "Warwick"},
    {"id": 498, "key": "Xayah"}, {"id": 101, "key": "Xerath"}, {"id": 5, "key": "XinZhao"},
    {"id": 157, "key": "Yasuo"}, {"id": 777, "key": "Yone"}, {"id": 83, "key": "Yorick"},
    {"id": 804, "key": "Yunara"}, {"id": 350, "key": "Yuumi"}, {"id": 904, "key": "Zaahen"},
    {"id": 154, "key": "Zac"}, {"id": 238, "key": "Zed"}, {"id": 221, "key": "Zeri"},
    {"id": 115, "key": "Ziggs"}, {"id": 26, "key": "Zilean"}, {"id": 142, "key": "Zoe"},
    {"id": 143, "key": "Zyra"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def get_tier(name):
    """获取强化等级"""
    return AUGMENT_TIERS.get(name, "gold")  # 默认 gold

def parse_augments_all_tiers(html_text):
    """解析所有等级的强化数据"""
    augments = {"silver": [], "gold": [], "prismatic": []}
    
    # 匹配表格中的强化数据
    # 格式: augment/xxx_large.png ... <strong>名称</strong> ... 百分比% ... 场次 Games
    pattern = r'augment/(\w+)_large\.png[^>]*>.*?<strong[^>]*>([^<]+)</strong>.*?<span class="font-bold">(\d+\.?\d*)%</span>.*?<span class="text-gray-500">(\d+(?:,\d+)*)'
    
    matches = re.findall(pattern, html_text, re.DOTALL)
    
    seen = set()
    for match in matches:
        icon_key = match[0]
        name = match[1].strip()
        # 处理 HTML 实体
        name = name.replace('&#x27;', "'")
        name = name.replace('&amp;', '&')
        
        # 跳过重复
        if name in seen:
            continue
        seen.add(name)
        
        pick_rate = float(match[2])
        games = int(match[3].replace(',', ''))
        
        if name and pick_rate > 0:
            tier = get_tier(name)
            augments[tier].append({
                "name": name,
                "icon": icon_key,
                "pickRate": pick_rate,
                "games": games
            })
    
    return augments

def parse_items(html_text):
    """解析 ARAM 装备数据"""
    items = {"core": [], "boots": [], "starter": []}
    
    # 核心装备
    core_match = re.search(r'Core Build.*?(?=Boots|Skill|$)', html_text, re.DOTALL | re.IGNORECASE)
    if core_match:
        core_items = re.findall(r'item/(\d+)\.png', core_match.group()[:2000])
        seen = set()
        for item in core_items:
            if item not in seen:
                seen.add(item)
                items["core"].append(item)
                if len(items["core"]) >= 3:
                    break
    
    # 鞋子
    boots_match = re.search(r'Boots.*?(?=Skill|Starter|Core|$)', html_text, re.DOTALL | re.IGNORECASE)
    if boots_match:
        boots_items = re.findall(r'item/(\d+)\.png', boots_match.group()[:1500])
        seen = set()
        for item in boots_items:
            if item not in seen:
                seen.add(item)
                items["boots"].append(item)
                if len(items["boots"]) >= 2:
                    break
    
    # 起始装备
    starter_match = re.search(r'Starter.*?(?=Core|Skill|Boots|$)', html_text, re.DOTALL | re.IGNORECASE)
    if starter_match:
        starter_items = re.findall(r'item/(\d+)\.png', starter_match.group()[:1500])
        seen = set()
        for item in starter_items:
            if item not in seen:
                seen.add(item)
                items["starter"].append(item)
                if len(items["starter"]) >= 2:
                    break
    
    return items

def fetch_champion_data(champion_key):
    """获取单个英雄的强化和装备数据"""
    url_key = champion_key.lower()
    url = f"https://www.op.gg/modes/arena/{url_key}/augments"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            augments = parse_augments_all_tiers(resp.text)
            items = parse_items(resp.text)
            return augments, items
        else:
            print(f"  HTTP {resp.status_code}")
            return None, None
    except Exception as e:
        print(f"  Error: {e}")
        return None, None

def test_single_champion():
    """测试单个英雄"""
    print("=== 测试 Katarina ===")
    augments, items = fetch_champion_data("Katarina")
    
    if augments:
        total = sum(len(v) for v in augments.values())
        print(f"✓ 成功获取 {total} 个强化:")
        for tier, aug_list in augments.items():
            print(f"  {tier}: {len(aug_list)} 个")
            for aug in aug_list[:3]:
                print(f"    - {aug['name']} ({aug['pickRate']}%)")
    else:
        print("✗ 强化获取失败!")
        return False
    
    if items["core"]:
        print(f"✓ 装备: 核心{items['core']}, 鞋子{items['boots']}")
    
    return True

def main():
    # 测试
    print("步骤1: 测试单个英雄...")
    if not test_single_champion():
        print("\n测试失败!")
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
    
    for i, champ in enumerate(CHAMPIONS):
        champ_id = str(champ["id"])
        champ_key = champ["key"]
        
        print(f"[{i+1}/{len(CHAMPIONS)}] {champ_key}...", end=" ", flush=True)
        
        augments, items = fetch_champion_data(champ_key)
        
        if augments:
            total = sum(len(v) for v in augments.values())
            result["data"][champ_id] = {
                "key": champ_key.lower(),
                "augments": augments,
                "items": items
            }
            print(f"✓ {total} 强化 (S:{len(augments['silver'])} G:{len(augments['gold'])} P:{len(augments['prismatic'])})")
            success_count += 1
        else:
            print("✗ 无数据")
            fail_count += 1
        
        time.sleep(1.0)
    
    # 保存
    output_path = Path(__file__).parent.parent / "data" / "augments.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！成功: {success_count}, 失败: {fail_count}")
    print(f"数据已保存到: {output_path}")

if __name__ == "__main__":
    main()

/**
 * 强化数据 - 包含中文名、等级、描述
 * 数据来源：英雄联盟斗魂竞技场/海克斯大乱斗 (Wiki官方数据)
 */

// 强化等级
export const AUGMENT_TIERS = {
  SILVER: 'silver',
  GOLD: 'gold',
  PRISMATIC: 'prismatic'
}

// 强化完整数据 - 根据 League Wiki 官方数据修正等级
export const augmentData = {
  // === 银色强化 (Silver) ===
  "404 Augment Not Found": { cn: "404强化未找到", tier: "silver", desc: "每回合获得3顶帽子" },
  "ADAPt": { cn: "法攻转换", tier: "silver", desc: "将所有额外攻击力转化为法术强度，并增加15%法术强度" },
  "Augmented Power": { cn: "强化之力", tier: "silver", desc: "强化和装备造成的伤害提高25%" },
  "Blunt Force": { cn: "钝击之力", tier: "silver", desc: "攻击力提高20%" },
  "Bravest of the Brave": { cn: "最勇敢的", tier: "silver", desc: "未来强化等级提升1级" },
  "Buff Buddies": { cn: "增益伙伴", tier: "silver", desc: "永久获得红蓝buff效果" },
  "Calculated Risk": { cn: "计算风险", tier: "silver", desc: "消耗所有重骰次数" },
  "Cannon Fodder": { cn: "炮灰", tier: "silver", desc: "战斗开始时从弹射器发射自己" },
  "Castle": { cn: "城堡", tier: "silver", desc: "与队友交换位置并获得护盾和移速" },
  "Clothesline": { cn: "晾衣绳", tier: "silver", desc: "与队友之间形成灼烧敌人的连线" },
  "Contract Killer": { cn: "契约杀手", tier: "silver", desc: "标记敌人使其受到更多伤害" },
  "Deft": { cn: "灵巧", tier: "silver", desc: "获得60%攻击速度" },
  "Dematerialize": { cn: "消解", tier: "silver", desc: "击杀英雄获得永久攻击力或法强" },
  "Desecrator": { cn: "亵渎者", tier: "silver", desc: "控制敌人获得诅咒之力转化为护甲魔抗" },
  "Dive Bomber": { cn: "俯冲轰炸机", tier: "silver", desc: "队伍首次死亡时造成爆炸伤害" },
  "Don't Blink": { cn: "别眨眼", tier: "silver", desc: "移速比目标高时造成更多伤害" },
  "Don't Chase": { cn: "别追", tier: "silver", desc: "获得辛吉德的毒气轨迹" },
  "Erosion": { cn: "侵蚀", tier: "silver", desc: "每次伤害降低敌人1.5%护甲和魔抗" },
  "EscAPADe": { cn: "攻法转换", tier: "silver", desc: "将法强转化为攻击力，并增加15%总攻击力" },
  "Executioner": { cn: "行刑者", tier: "silver", desc: "对低于50%生命值的敌人造成15%额外伤害" },
  "Fallen Aegis": { cn: "堕落神盾", tier: "silver", desc: "战斗开始时获得魔法护盾和控制免疫" },
  "Firefox": { cn: "火狐", tier: "silver", desc: "自动释放阿狸的狐火" },
  "Fire Sale": { cn: "清仓大甩卖", tier: "silver", desc: "卖掉所有装备获得更高金币" },
  "First-Aid Kit": { cn: "急救包", tier: "silver", desc: "获得20%治疗护盾强度" },
  "Flashbang": { cn: "闪光弹", tier: "silver", desc: "闪现时造成伤害和减速" },
  "Frost Wraith": { cn: "冰霜幽灵", tier: "silver", desc: "自动释放丽桑卓的冰环" },
  "Frozen Foundations": { cn: "冰冻根基", tier: "silver", desc: "召唤冰墙击退敌人" },
  "Fruits of Your Labor": { cn: "劳动果实", tier: "silver", desc: "能量花效果提高25%" },
  "Goredrink": { cn: "血饮", tier: "silver", desc: "获得20%全能吸血" },
  "Guilty Pleasure": { cn: "罪恶快感", tier: "silver", desc: "控制敌人时治疗自己" },
  "Heavy Hitter": { cn: "重击者", tier: "silver", desc: "普攻造成3.5%最大生命值额外伤害" },
  "Hold Very Still": { cn: "保持静止", tier: "silver", desc: "获得提莫的隐身被动" },
  "Homeguard": { cn: "家园卫士", tier: "silver", desc: "获得100%移速，战斗时失效" },
  "Ice Cold": { cn: "冰冷", tier: "silver", desc: "减速效果额外降低100移速" },
  "Infernal Soul": { cn: "炼狱之魂", tier: "silver", desc: "获得炼狱龙魂" },
  "Juice Box": { cn: "果汁盒", tier: "silver", desc: "每回合免费获得一瓶果汁" },
  "Juice Press": { cn: "果汁机", tier: "silver", desc: "果汁价格降低50%" },
  "Leg Day": { cn: "腿部训练日", tier: "silver", desc: "获得50移速和40%减速抗性" },
  "Light 'em Up": { cn: "点燃他们", tier: "silver", desc: "每4次攻击发射烟花造成额外伤害" },
  "Mind to Matter": { cn: "心智转化", tier: "silver", desc: "获得等于50%最大法力值的生命值" },
  "Mirror Image": { cn: "镜像", tier: "silver", desc: "生命值降低时创建分身并隐身" },
  "Mountain Soul": { cn: "山脉之魂", tier: "silver", desc: "获得山脉龙魂" },
  "Now You See Me": { cn: "现在你看到我了", tier: "silver", desc: "位移后留下标记，可传送回去" },
  "Numb to Pain": { cn: "麻木", tier: "silver", desc: "获得死亡之舞的伤害延迟效果" },
  "Ocean Soul": { cn: "海洋之魂", tier: "silver", desc: "获得海洋龙魂" },
  "Parasitic Mutation": { cn: "寄生突变", tier: "silver", desc: "复制敌方随机强化" },
  "Repulsor": { cn: "排斥者", tier: "silver", desc: "生命值降低时击退周围敌人" },
  "Scoped Weapons": { cn: "瞄准武器", tier: "silver", desc: "增加攻击距离" },
  "Self Destruct": { cn: "自毁", tier: "silver", desc: "15秒后爆炸造成真实伤害" },
  "Serve Beyond Death": { cn: "死后服务", tier: "silver", desc: "首次致死伤害后恢复满血但持续掉血" },
  "Shadow Runner": { cn: "暗影奔跑者", tier: "silver", desc: "位移或脱离隐身后获得300移速" },
  "Slap Around": { cn: "拍打", tier: "silver", desc: "控制敌人获得永久攻击力或法强" },
  "Slime Time": { cn: "史莱姆时间", tier: "silver", desc: "自动释放扎克的不稳定物质" },
  "Snowball Fight!": { cn: "雪球大战", tier: "silver", desc: "获得雪球技能" },
  "Sonic Boom": { cn: "音爆", tier: "silver", desc: "给队友增益时对周围敌人造成伤害" },
  "Spin To Win": { cn: "旋转获胜", tier: "silver", desc: "旋转技能伤害提高30%并获得30技能急速" },
  "Spirit Infusion": { cn: "精神灌注", tier: "silver", desc: "大招后治疗护盾强度提高50%" },
  "Stackosaurus Rex": { cn: "叠加暴龙", tier: "silver", desc: "技能获得的永久层数提高75%" },
  "Stats!": { cn: "属性！", tier: "silver", desc: "获得2个属性铁砧" },
  "Tank It Or Leave It": { cn: "坦克或离开", tier: "silver", desc: "获得暴击防御几率" },
  "Tormentor": { cn: "折磨者", tier: "silver", desc: "控制敌人时施加灼烧" },
  "Trailblazer": { cn: "开拓者", tier: "silver", desc: "位移时对最近敌人施加灼烧" },
  "Transmute: Gold": { cn: "转化：金色", tier: "silver", desc: "获得一个随机金色强化" },
  "Typhoon": { cn: "台风", tier: "silver", desc: "普攻额外攻击一个目标" },
  "Ultimate Unstoppable": { cn: "大招无阻", tier: "silver", desc: "释放大招获得3秒控制免疫" },
  "Warmup Routine": { cn: "热身程序", tier: "silver", desc: "引导增加伤害输出" },
  "Witchful Thinking": { cn: "巫术思维", tier: "silver", desc: "获得70法术强度" },

  // === 金色强化 (Gold) ===
  "All For You": { cn: "为你而战", tier: "gold", desc: "对队友的治疗和护盾效果提高30%" },
  "And My Axe!": { cn: "还有我的斧头！", tier: "gold", desc: "自动投掷奥拉夫的斧头" },
  "Apex Inventor": { cn: "顶尖发明家", tier: "gold", desc: "获得300装备技能急速" },
  "Banner of Command": { cn: "指挥旗帜", tier: "gold", desc: "给队友增加15%属性" },
  "Big Brain": { cn: "大脑袋", tier: "gold", desc: "战斗开始时获得等于300%法强的护盾" },
  "Blood Brother": { cn: "血脉兄弟", tier: "gold", desc: "获得德莱厄斯的出血被动" },
  "Bodyguard": { cn: "保镖", tier: "gold", desc: "位移时获得护盾，经过队友也给他们护盾" },
  "Bread And Butter": { cn: "黄油面包", tier: "gold", desc: "Q技能获得200技能急速" },
  "Bread And Cheese": { cn: "芝士面包", tier: "gold", desc: "E技能获得200技能急速" },
  "Bread And Jam": { cn: "果酱面包", tier: "gold", desc: "W技能获得200技能急速" },
  "Celestial Body": { cn: "天体之躯", tier: "gold", desc: "获得1250生命值但伤害降低10%" },
  "Combo Master": { cn: "连招大师", tier: "gold", desc: "获得电刑和相位猛冲符文" },
  "Critical Healing": { cn: "暴击治疗", tier: "gold", desc: "治疗和护盾有几率暴击，获得25%暴击" },
  "Dark Blessing": { cn: "黑暗祝福", tier: "gold", desc: "治疗或护盾队友获得诅咒之力" },
  "Dawnbringer's Resolve": { cn: "黎明使者的决心", tier: "gold", desc: "首次降到50%血量时恢复30%最大生命值" },
  "Deathtouch": { cn: "死亡之触", tier: "gold", desc: "普攻获得诅咒之力，转化为攻击附魔" },
  "Defensive Maneuvers": { cn: "防御机动", tier: "gold", desc: "获得屏障和治疗双召唤师技能" },
  "Demon's Dance": { cn: "恶魔之舞", tier: "gold", desc: "获得迅捷步伐和不灭之握符文" },
  "Die Another Day": { cn: "择日再死", tier: "gold", desc: "创建保护区域，区域内单位不会死亡" },
  "Divine Intervention": { cn: "神圣干预", tier: "gold", desc: "自动释放塔里克的大招" },
  "Ethereal Weapon": { cn: "虚灵武器", tier: "gold", desc: "技能可以触发攻击特效" },
  "Extendo-Arm": { cn: "伸缩手臂", tier: "gold", desc: "自动释放布里茨的钩子" },
  "Firebrand": { cn: "火焰烙印", tier: "gold", desc: "普攻施加灼烧效果" },
  "Flashy": { cn: "闪耀", tier: "gold", desc: "闪现有3层充能" },
  "From Beginning to End": { cn: "从始至终", tier: "gold", desc: "获得黑暗收割和先攻符文" },
  "Hat Trick": { cn: "帽子戏法", tier: "gold", desc: "获得3顶帽子，低血量时获得护盾" },
  "Holy Fire": { cn: "圣火", tier: "gold", desc: "治疗和护盾时对敌人施加灼烧" },
  "Impassable": { cn: "不可逾越", tier: "gold", desc: "获得余震和冰川增幅符文" },
  "It's Critical": { cn: "暴击时刻", tier: "gold", desc: "获得50%暴击几率" },
  "It's Killing Time": { cn: "杀戮时刻", tier: "gold", desc: "大招对所有敌人施加劫的死亡印记" },
  "Keystone Conjurer": { cn: "基石召唤师", tier: "gold", desc: "获得奥术彗星和艾黎符文" },
  "Light Warden": { cn: "光明守望者", tier: "gold", desc: "自动释放拉克丝的护盾" },
  "Lightning Strikes": { cn: "闪电打击", tier: "gold", desc: "攻速加成提高20%，满攻速时普攻附魔" },
  "Magic Missile": { cn: "魔法飞弹", tier: "gold", desc: "技能命中发射3枚飞弹造成真实伤害" },
  "Marksmage": { cn: "法师射手", tier: "gold", desc: "普攻造成100%法强的额外物理伤害" },
  "Minionmancer": { cn: "仆从法师", tier: "gold", desc: "宠物伤害和生命值提高40%" },
  "OK Boomerang": { cn: "回旋镖", tier: "gold", desc: "自动释放希维尔的回旋镖" },
  "Oathsworn": { cn: "誓约", tier: "gold", desc: "获得卡莉斯塔的大招" },
  "Outlaw's Grit": { cn: "亡命之徒的勇气", tier: "gold", desc: "位移时获得护甲和魔抗叠加" },
  "Overflow": { cn: "溢出", tier: "gold", desc: "法力消耗翻倍但伤害和治疗提高" },
  "Parasitic Relationship": { cn: "寄生关系", tier: "gold", desc: "队友造成伤害时治疗你" },
  "Perseverance": { cn: "坚韧不拔", tier: "gold", desc: "获得800%基础生命回复" },
  "Phenomenal Evil": { cn: "非凡邪恶", tier: "gold", desc: "获得维迦的被动，技能命中获得法强" },
  "Quest: Angel of Retribution": { cn: "任务：复仇天使", tier: "gold", desc: "治疗队友2500后获得攻速和附魔" },
  "Quest: Mad Hatter": { cn: "任务：疯帽匠", tier: "gold", desc: "同时戴10顶帽子获得属性加成" },
  "Quest: Steel Your Heart": { cn: "任务：钢铁之心", tier: "gold", desc: "获得心钢并叠加400生命值后强化" },
  "Quest: Three Sacred Treasures": { cn: "任务：三神器", tier: "gold", desc: "拥有海克斯科技枪刃、无尽之刃和困惑" },
  "Quest: Urf's Champion": { cn: "任务：阿福的冠军", tier: "gold", desc: "击杀8个英雄后获得金铲子" },
  "Rabble Rousing": { cn: "煽动群众", tier: "gold", desc: "释放技能时治疗自己" },
  "Recursion": { cn: "递归", tier: "gold", desc: "获得60技能急速" },
  "Restart": { cn: "重启", tier: "gold", desc: "每10秒刷新基础技能冷却" },
  "Restless Restoration": { cn: "不安的恢复", tier: "gold", desc: "移动时持续治疗" },
  "Scopier Weapons": { cn: "瞄准武器+", tier: "gold", desc: "大幅增加攻击距离" },
  "Searing Dawn": { cn: "灼热黎明", tier: "gold", desc: "获得蕾欧娜的阳光被动" },
  "Shrink Ray": { cn: "缩小射线", tier: "gold", desc: "普攻降低目标15%伤害和体型" },
  "Skilled Sniper": { cn: "精准狙击手", tier: "gold", desc: "远距离命中技能刷新冷却" },
  "Slow and Steady": { cn: "稳扎稳打", tier: "gold", desc: "攻速固定为1.0但转化为攻击力" },
  "Soul Siphon": { cn: "灵魂虹吸", tier: "gold", desc: "暴击治疗12%伤害，获得25%暴击" },
  "Stats on Stats!": { cn: "属性叠加！", tier: "gold", desc: "获得3个属性铁砧" },
  "Summoner Revolution": { cn: "召唤师革命", tier: "gold", desc: "首次使用召唤师技能冷却变为3秒" },
  "Symbiotic Mutation": { cn: "共生突变", tier: "gold", desc: "复制队友随机强化" },
  "Tank Engine": { cn: "坦克引擎", tier: "gold", desc: "击杀英雄获得5%最大生命值和15%体型" },
  "The Brutalizer": { cn: "残暴之力", tier: "gold", desc: "获得25攻击力、10技能急速、5穿透" },
  "Thread the Needle": { cn: "穿针引线", tier: "gold", desc: "获得20%护甲和魔抗穿透" },
  "Transmute: Prismatic": { cn: "转化：棱彩", tier: "gold", desc: "获得一个随机棱彩强化" },
  "Trickster Demon": { cn: "诡术恶魔", tier: "gold", desc: "脱离隐身时造成爆炸伤害" },
  "Twice Thrice": { cn: "双倍三倍", tier: "gold", desc: "每2次攻击额外触发150%攻击特效" },
  "Undying Guard": { cn: "不死守卫", tier: "gold", desc: "复活时造成伤害并获得无敌" },
  "Vanish": { cn: "消失", tier: "gold", desc: "获得4秒隐身技能" },
  "Vengeance": { cn: "复仇", tier: "gold", desc: "队友死后获得28%伤害和全能吸血" },
  "Vulnerability": { cn: "弱点暴露", tier: "gold", desc: "装备和持续伤害可以暴击" },
  "We'll Be Right Back": { cn: "马上回来", tier: "gold", desc: "进入金身并冻结周围敌人" },
  "Willing Sacrifice": { cn: "甘愿牺牲", tier: "gold", desc: "队友低血量时牺牲自己血量给护盾" },
  "With Haste": { cn: "急速前进", tier: "gold", desc: "获得等于150%技能急速的移速" },

  // === 棱彩强化 (Prismatic) ===
  "Accelerating Sorcery": { cn: "加速魔法", tier: "prismatic", desc: "释放技能获得12技能急速，无限叠加" },
  "Augment 405": { cn: "强化405", tier: "prismatic", desc: "每顶帽子增加5%伤害" },
  "Back to Basics": { cn: "返璞归真", tier: "prismatic", desc: "伤害和治疗提高35%但大招被封印" },
  "Blade Waltz": { cn: "剑舞", tier: "prismatic", desc: "获得菲奥娜的大招位移" },
  "Can't Touch This": { cn: "碰不到我", tier: "prismatic", desc: "大招后获得2秒无敌" },
  "Center of the Universe": { cn: "宇宙中心", tier: "prismatic", desc: "获得奥瑞利安索尔的星星被动" },
  "Cerberus": { cn: "地狱三头犬", tier: "prismatic", desc: "获得致命节奏和迅捷步伐符文" },
  "Chain Lightning": { cn: "连锁闪电", tier: "prismatic", desc: "伤害会弹射到附近敌人" },
  "Chauffeur": { cn: "司机", tier: "prismatic", desc: "附着在队友身上，获得技能急速和攻速" },
  "Circle of Death": { cn: "死亡之环", tier: "prismatic", desc: "治疗转化为对敌人的伤害" },
  "Clown College": { cn: "小丑学院", tier: "prismatic", desc: "获得沙科的被动、Q和大招爆炸" },
  "Courage of the Colossus": { cn: "巨像勇气", tier: "prismatic", desc: "控制敌人获得护盾" },
  "Dashing": { cn: "冲刺", tier: "prismatic", desc: "位移技能获得300技能急速" },
  "Doomsayer": { cn: "末日预言者", tier: "prismatic", desc: "技能伤害获得诅咒之力" },
  "Draw Your Sword": { cn: "拔剑", tier: "prismatic", desc: "变成近战获得大量属性加成" },
  "Dreadbringer": { cn: "恐惧使者", tier: "prismatic", desc: "靠近敌人获得诅咒之力转化为生命值" },
  "Dual Wield": { cn: "双持", tier: "prismatic", desc: "普攻额外发射一发弹道" },
  "Earthwake": { cn: "地震", tier: "prismatic", desc: "位移后留下爆炸轨迹" },
  "Eureka": { cn: "尤里卡", tier: "prismatic", desc: "获得等于30%法强的技能急速" },
  "Fan the Hammer": { cn: "扇形射击", tier: "prismatic", desc: "每个方向首次攻击发射5发子弹" },
  "Feel the Burn": { cn: "感受灼烧", tier: "prismatic", desc: "对周围敌人释放虚弱和点燃" },
  "Fey Magic": { cn: "精灵魔法", tier: "prismatic", desc: "大招命中敌人变成小动物2秒" },
  "Gamba Anvil": { cn: "赌博铁砧", tier: "prismatic", desc: "获得1000金币，棱彩装备降价" },
  "Giant Slayer": { cn: "巨人杀手", tier: "prismatic", desc: "变小获得移速，对大体型敌人伤害提高" },
  "Goliath": { cn: "歌利亚", tier: "prismatic", desc: "获得35%最大生命值、15%自适应和50%体型" },
  "Infernal Conduit": { cn: "炼狱导管", tier: "prismatic", desc: "技能施加灼烧，灼烧减少技能冷却" },
  "Jeweled Gauntlet": { cn: "珠光护手", tier: "prismatic", desc: "技能可以暴击，获得暴击几率" },
  "Laser Eyes": { cn: "激光眼", tier: "prismatic", desc: "持续发射激光造成伤害" },
  "Mad Scientist": { cn: "疯狂科学家", tier: "prismatic", desc: "战斗开始随机获得大或小的属性加成" },
  "Master of Duality": { cn: "双重大师", tier: "prismatic", desc: "普攻获得法强，技能获得攻击力" },
  "Mystic Punch": { cn: "神秘拳击", tier: "prismatic", desc: "普攻减少技能20%剩余冷却" },
  "Nesting Doll": { cn: "套娃", tier: "prismatic", desc: "可以复活2次但每次变小" },
  "Null": { cn: "空", tier: "prismatic", desc: "无效果（寄生突变失败时获得）" },
  "Omni Soul": { cn: "全能之魂", tier: "prismatic", desc: "获得3个随机龙魂" },
  "Orbital Laser": { cn: "轨道激光", tier: "prismatic", desc: "召唤激光轰炸指定区域" },
  "Pandora's Box": { cn: "潘多拉魔盒", tier: "prismatic", desc: "当前强化变成随机棱彩强化" },
  "Prismatic Egg": { cn: "棱彩之蛋", tier: "prismatic", desc: "每5次击杀获得棱彩装备铁砧" },
  "Quantum Computing": { cn: "量子计算", tier: "prismatic", desc: "自动释放卡蜜尔的W技能" },
  "Quest: Wooglet's Witchcap": { cn: "任务：沃格莱特的巫帽", tier: "prismatic", desc: "获得大棒，合成帽子和沙漏后融合" },
  "Raid Boss": { cn: "团本首领", tier: "prismatic", desc: "战斗开始被囚禁但获得大量属性" },
  "Scopiest Weapons": { cn: "瞄准武器++", tier: "prismatic", desc: "极大增加攻击距离" },
  "Slow Cooker": { cn: "慢炖锅", tier: "prismatic", desc: "周围敌人持续受到灼烧" },
  "Spellwake": { cn: "法术尾迹", tier: "prismatic", desc: "技能命中后留下爆炸轨迹" },
  "Spirit Link": { cn: "灵魂链接", tier: "prismatic", desc: "分担队友15%伤害，获得其50%治疗" },
  "Stats on Stats on Stats!": { cn: "属性叠叠叠！", tier: "prismatic", desc: "获得4个属性铁砧" },
  "Summoner's Roulette": { cn: "召唤师轮盘", tier: "prismatic", desc: "召唤师技能随机变化" },
  "Symphony of War": { cn: "战争交响曲", tier: "prismatic", desc: "获得征服者和致命节奏符文" },
  "Tap Dancer": { cn: "踢踏舞者", tier: "prismatic", desc: "普攻叠加移速，移速转化为攻速" },
  "Transmute: Chaos": { cn: "转化：混沌", tier: "prismatic", desc: "获得2个随机强化" },
  "Trueshot Prodigy": { cn: "精准神射", tier: "prismatic", desc: "远距离命中敌人释放伊泽瑞尔大招" },
  "Ultimate Revolution": { cn: "大招革命", tier: "prismatic", desc: "大招释放后立即刷新冷却" },
  "Ultimate Roulette": { cn: "大招轮盘", tier: "prismatic", desc: "获得随机英雄的大招" },
  "Wisdom of Ages": { cn: "岁月智慧", tier: "prismatic", desc: "获得1级并每隔一回合再获得1级" },
}

/**
 * 获取强化的中文名称
 */
export function getAugmentChineseName(englishName) {
  return augmentData[englishName]?.cn || englishName
}

/**
 * 获取强化等级
 */
export function getAugmentTier(englishName) {
  return augmentData[englishName]?.tier || 'silver'
}

/**
 * 获取强化描述
 */
export function getAugmentDescription(englishName) {
  return augmentData[englishName]?.desc || ''
}

/**
 * 获取强化图标 URL
 * @param {string} iconKeyOrName - 图标 key（如 "thebrutalizer"）或强化名称（如 "The Brutalizer"）
 */
export function getAugmentIconUrl(iconKeyOrName) {
  if (!iconKeyOrName) return ''
  
  let iconKey = iconKeyOrName
  
  // 如果包含大写字母、空格或特殊字符，说明是强化名称，需要转换
  if (/[A-Z\s':!]/.test(iconKeyOrName)) {
    iconKey = iconKeyOrName
      .replace(/[':!]/g, '')  // 移除特殊字符
      .replace(/\s+/g, '')    // 移除空格
      .toLowerCase()          // 转小写
  }
  
  return `https://opgg-static.akamaized.net/meta/images/lol/latest/augment/${iconKey}_large.png`
}

/**
 * 获取等级对应的颜色
 */
export function getTierColor(tier) {
  const colors = {
    silver: '#A8B4C4',
    gold: '#FFD700',
    prismatic: '#E066FF'
  }
  return colors[tier] || colors.silver
}

/**
 * 获取等级中文名
 */
export function getTierName(tier) {
  const names = {
    silver: '银色',
    gold: '金色',
    prismatic: '棱彩'
  }
  return names[tier] || '银色'
}

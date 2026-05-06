"""Fetch ARAM: Mayhem augment data by scraping OP.GG web pages."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch ARAM: Mayhem augments from OP.GG")
    parser.add_argument("--output", default="data/augments.json", help="Output file")
    parser.add_argument("--sleep", type=float, default=1.0, help="Delay between requests")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout seconds")
    parser.add_argument("--version", default="16.05", help="Optional output version")
    parser.add_argument("--region", default="global", help="Region (global/kr/etc)")
    return parser.parse_args()


def load_champions(project_root: Path) -> list[dict]:
    """Load champions from frontend data file."""
    champions_path = project_root / "frontend" / "src" / "data" / "champions.js"
    if not champions_path.exists():
        champions_path = project_root / "lol-assistant" / "frontend" / "src" / "data" / "champions.js"
    
    source = champions_path.read_text(encoding="utf-8", errors="ignore")

    pattern = re.compile(r"\{\s*id:\s*(\d+)\s*,\s*key:\s*'([^']+)'", re.MULTILINE)
    champions: list[dict] = []
    seen_ids: set[int] = set()

    for match in pattern.finditer(source):
        champion_id = int(match.group(1))
        champion_key = match.group(2)
        if champion_id in seen_ids:
            continue
        seen_ids.add(champion_id)
        champions.append({"id": champion_id, "key": champion_key})

    if not champions:
        raise RuntimeError("No champions parsed from champions.js")

    return champions


def load_augment_mapping(timeout_seconds: int) -> tuple[dict[int, str], dict[int, str]]:
    """Load augment id->name and id->tier map from CDragon."""
    mapping_url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/cherry-augments.json"
    response = requests.get(mapping_url, headers=HEADERS, timeout=timeout_seconds)
    response.raise_for_status()

    id_to_name: dict[int, str] = {}
    id_to_tier: dict[int, str] = {}

    for augment in response.json():
        augment_id = augment.get("id")
        augment_name = augment.get("nameTRA") or augment.get("name")
        rarity = str(augment.get("rarity", "")).lower()

        if not augment_id or not augment_name:
            continue

        id_to_name[int(augment_id)] = str(augment_name)

        if "prismatic" in rarity:
            id_to_tier[int(augment_id)] = "prismatic"
        elif "silver" in rarity:
            id_to_tier[int(augment_id)] = "silver"
        else:
            id_to_tier[int(augment_id)] = "gold"

    return id_to_name, id_to_tier


def create_name_to_id_map(id_to_name: dict[int, str]) -> dict[str, int]:
    """Create a reverse map from name to id."""
    name_to_id = {}
    for aug_id, name in id_to_name.items():
        name_to_id[name.lower()] = aug_id
    return name_to_id


def fetch_one(champion_key: str, timeout_seconds: int) -> dict | None:
    """Fetch ARAM: Mayhem page for one champion."""
    url = f"https://www.op.gg/lol/modes/aram-mayhem/{champion_key.lower()}/augments"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout_seconds)
        if response.status_code == 200:
            return response.text
        return None
    except Exception:
        return None


def parse_augments_from_html(html: str) -> dict:
    """Parse augment data from OP.GG HTML page.
    
    The HTML contains augment data in escaped JSON format within script tags.
    """
    result = {"silver": [], "gold": [], "prismatic": []}
    
    import re
    
    if not html:
        return result
    
    # Pattern with escaped quotes \"id\":NUMBER
    pattern = r'\\"id\\":(\d+),\\"tier\\":(\d+),\\"performance\\":([\d.]+),\\"popular\\":([\d.]+),\\"name\\":\\"([^\\]+)\\"'
    matches = re.findall(pattern, html)
    
    if not matches:
        return result
    
    # Map tier values to tier names
    TIER_MAP = {
        0: "silver",
        1: "silver", 
        2: "gold",
        3: "gold",
        4: "prismatic",
        5: "prismatic",
    }
    
    for match in matches:
        aug_id = int(match[0])
        tier_num = int(match[1])
        performance = float(match[2])
        popularity = float(match[3])
        aug_name = match[4]
        
        tier = TIER_MAP.get(tier_num, "gold")
        
        result[tier].append({
            "id": aug_id,
            "name": aug_name,
            "pickRate": round(popularity, 2),
            "winRate": round(performance, 2),
            "games": 0,
        })
    
    # Sort by win rate
    for tier in ("silver", "gold", "prismatic"):
        result[tier].sort(key=lambda item: (item.get("winRate", 0), item.get("games", 0)), reverse=True)
    
    return result


def parse_summary_from_html(html: str) -> dict:
    """Parse champion summary data from HTML."""
    summary = {"play": 0, "win_rate": 0, "pick_rate": 0}
    
    # Look for summary data patterns in the HTML
    # Try to find win_rate and pick_rate
    win_match = re.search(r'"win_rate"\s*:\s*([\d.]+)', html)
    pick_match = re.search(r'"pick_rate"\s*:\s*([\d.]+)', html)
    play_match = re.search(r'"play"\s*:\s*(\d+)', html)
    
    if win_match:
        summary["win_rate"] = round(float(win_match.group(1)) * 100, 2)
    if pick_match:
        summary["pick_rate"] = round(float(pick_match.group(1)) * 100, 2)
    if play_match:
        summary["play"] = int(play_match.group(1))
    
    return summary


def main():
    args = parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    if (project_root / "lol-assistant").exists():
        project_root = project_root / "lol-assistant"

    print(f"Project root: {project_root}")
    
    # Load champions
    champions = load_champions(project_root)
    print(f"Loaded {len(champions)} champions")
    
    # Load augment mapping (for ID to name mapping if needed)
    print("Loading augment mapping from CDragon...")
    try:
        id_to_name, id_to_tier = load_augment_mapping(args.timeout)
        print(f"Loaded {len(id_to_name)} augments")
    except Exception as e:
        print(f"Warning: Could not load augment mapping: {e}")
        id_to_name = {}
        id_to_tier = {}
    
    # Fetch data for each champion
    result = {
        "version": args.version,
        "updateTime": time.strftime("%Y-%m-%d %H:%M:%S"),
        "meta": {
            "region": args.region,
            "source": "OP.GG ARAM: Mayhem (scraped)",
            "champions": len(champions),
            "mode": "aram-mayhem"
        },
        "data": {}
    }
    
    # Test with first champion first
    print("\nTesting with Pantheon...")
    html = fetch_one("Pantheon", args.timeout)
    if html:
        augments = parse_augments_from_html(html)
        total = sum(len(a) for a in augments.values())
        print(f"Pantheon: {total} augments (S:{len(augments['silver'])}, G:{len(augments['gold'])}, P:{len(augments['prismatic'])})")
        
        # Show first few augments
        for tier in ["silver", "gold", "prismatic"]:
            if augments[tier]:
                print(f"  {tier}: {augments[tier][0]['name']} (WR:{augments[tier][0]['winRate']}%)")
    
    # Process all champions
    print(f"\nFetching all {len(champions)} champions...")
    for i, champ in enumerate(champions):
        champ_key = champ["key"]
        champ_id = champ["id"]
        
        print(f"[{i+1}/{len(champions)}] {champ_key}...", end=" ", flush=True)
        
        html = fetch_one(champ_key, args.timeout)
        
        if html:
            augments = parse_augments_from_html(html)
            summary = parse_summary_from_html(html)
            
            total_augs = sum(len(a) for a in augments.values())
            
            if total_augs > 0:
                result["data"][str(champ_id)] = {
                    "key": champ_key,
                    "summary": summary,
                    "augments": augments
                }
                print(f"OK ({total_augs})")
            else:
                print("No data")
        else:
            print("Failed")
        
        time.sleep(args.sleep)
    
    # Save to file
    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nData saved to {output_path}")
    print(f"Total champions with data: {len(result['data'])}")


if __name__ == "__main__":
    main()

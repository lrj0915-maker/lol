"""Fetch arena augment data from OP.GG API with dynamic champion source."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

RARITY_TO_TIER = {
    1: "silver",
    4: "gold",
    8: "prismatic",
    16: "prismatic",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch arena augments from OP.GG")
    parser.add_argument("--region", default="GLOBAL", help="API region, e.g. GLOBAL/KR")
    parser.add_argument("--output", default="data/augments.json", help="Output file")
    parser.add_argument("--sleep", type=float, default=0.25, help="Delay between requests")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout seconds")
    parser.add_argument("--retries", type=int, default=2, help="Retries per champion")
    parser.add_argument("--version", default="", help="Optional output version")
    return parser.parse_args()


def load_champions(project_root: Path) -> list[dict]:
    champions_path = project_root / "frontend" / "src" / "data" / "champions.js"
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
        raise RuntimeError("No champions parsed from frontend/src/data/champions.js")

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


def fetch_one(champion_key: str, region: str, timeout_seconds: int, retries: int) -> dict | None:
    url = f"https://lol-api-champion.op.gg/api/{region}/champions/arena/{champion_key.lower()}"

    for attempt in range(1, max(1, retries) + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout_seconds)
            if response.status_code == 200:
                return response.json()
            if response.status_code in (404, 422):
                return None
            if response.status_code == 429:
                time.sleep(min(2.0, 0.4 * attempt))
                continue
        except Exception:
            time.sleep(min(2.0, 0.4 * attempt))

    return None


def safe_rate(numerator: float, denominator: float) -> float:
    denominator_value = float(denominator or 0)
    if denominator_value <= 0:
        return 0.0
    return (float(numerator or 0) / denominator_value) * 100


def parse_augments(api_payload: dict, id_to_name: dict[int, str], id_to_tier: dict[int, str]) -> dict:
    result = {"silver": [], "gold": [], "prismatic": []}

    data = (api_payload or {}).get("data") or {}
    groups = data.get("augment_group") or []

    for group in groups:
        rarity_value = int(group.get("rarity") or 0)
        group_tier = RARITY_TO_TIER.get(rarity_value, "gold")

        for augment in group.get("augments") or []:
            augment_id = int(augment.get("id") or 0)
            if augment_id <= 0:
                continue

            tier = id_to_tier.get(augment_id, group_tier)
            tier = tier if tier in result else group_tier

            play_count = int(augment.get("play") or 0)
            win_count = int(augment.get("win") or 0)

            result[tier].append(
                {
                    "id": augment_id,
                    "name": id_to_name.get(augment_id, f"Augment_{augment_id}"),
                    "pickRate": round(float(augment.get("pick_rate") or 0) * 100, 2),
                    "winRate": round(safe_rate(win_count, play_count), 2),
                    "games": play_count,
                }
            )

    for tier in ("silver", "gold", "prismatic"):
        result[tier].sort(key=lambda item: (item.get("winRate", 0), item.get("games", 0)), reverse=True)

    return result


def parse_items(api_payload: dict) -> dict:
    data = (api_payload or {}).get("data") or {}
    return {
        "core": data.get("core_items") or [],
        "boots": data.get("boots") or [],
        "starter": data.get("starter_items") or [],
    }


def parse_summary(api_payload: dict) -> dict:
    data = (api_payload or {}).get("data") or {}
    summary = data.get("summary") or {}
    average_stats = summary.get("average_stats") or {}

    return {
        "play": int(average_stats.get("play") or 0),
        "win_rate": round(float(average_stats.get("win_rate") or 0) * 100, 2),
        "pick_rate": round(float(average_stats.get("pick_rate") or 0) * 100, 2),
        "ban_rate": round(float(average_stats.get("ban_rate") or 0) * 100, 2),
    }


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    region = str(args.region or "GLOBAL").upper().strip() or "GLOBAL"
    champions = load_champions(project_root)

    id_to_name, id_to_tier = load_augment_mapping(args.timeout)
    print(f"[Augments] loaded champion pool: {len(champions)}")
    print(f"[Augments] loaded mapping size: {len(id_to_name)}")
    print(f"[Augments] source region: {region}")

    result = {
        "version": args.version or time.strftime("%Y.%m.%d"),
        "updateTime": time.strftime("%Y-%m-%d %H:%M:%S"),
        "meta": {
            "region": region,
            "source": "OP.GG arena API",
            "champions": len(champions),
        },
        "data": {},
    }

    success_count = 0
    fail_count = 0
    discovered_version = ""

    for index, champion in enumerate(champions, start=1):
        champion_id = str(champion["id"])
        champion_key = str(champion["key"])

        payload = fetch_one(champion_key, region, args.timeout, args.retries)
        if not payload:
            fail_count += 1
            print(f"[{index:>3}/{len(champions)}] {champion_key:<16} NO_DATA")
            time.sleep(max(0.0, float(args.sleep)))
            continue

        if not discovered_version:
            discovered_version = str((payload.get("meta") or {}).get("version") or "")

        augments = parse_augments(payload, id_to_name, id_to_tier)
        result["data"][champion_id] = {
            "key": champion_key.lower(),
            "summary": parse_summary(payload),
            "augments": augments,
            "items": parse_items(payload),
        }

        success_count += 1
        total_augments = sum(len(augments[tier]) for tier in ("silver", "gold", "prismatic"))
        print(f"[{index:>3}/{len(champions)}] {champion_key:<16} OK ({total_augments})")
        time.sleep(max(0.0, float(args.sleep)))

    if discovered_version and not args.version:
        result["version"] = discovered_version

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 64)
    print(f"Done | success={success_count} failed={fail_count} total={len(champions)}")
    print(f"Saved: {output_path}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


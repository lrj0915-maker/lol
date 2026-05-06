"""从 OP.GG Ranked API 抓取符文推荐数据。"""

from __future__ import annotations

import argparse
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DEFAULT_POSITIONS = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
REGION_ALIASES = {
    "CN": "GLOBAL",
    "ZH": "GLOBAL",
}
SUPPORTED_REGIONS = {
    "GLOBAL",
    "KR",
    "JP",
    "NA",
    "EUW",
    "EUNE",
    "BR",
    "LAN",
    "LAS",
    "OCE",
    "TR",
    "RU",
    "TW",
    "VN",
    "PH",
    "SG",
    "TH",
    "ME",
}
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


@dataclass
class Champion:
    id: int
    key: str


class SharedRateLimiter:
    def __init__(self, min_interval_seconds: float):
        self._min_interval_seconds = max(0.0, float(min_interval_seconds))
        self._lock = threading.Lock()
        self._last_request_at = 0.0

    def wait_turn(self):
        if self._min_interval_seconds <= 0:
            return
        with self._lock:
            now = time.time()
            wait_seconds = self._min_interval_seconds - (now - self._last_request_at)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            self._last_request_at = time.time()


def create_retry_session(retries: int, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def parse_positions(raw_positions: str) -> list[str]:
    positions = [position.strip().upper() for position in raw_positions.split(",") if position.strip()]
    if not positions:
        return DEFAULT_POSITIONS
    invalid = [position for position in positions if position not in DEFAULT_POSITIONS]
    if invalid:
        raise ValueError(f"invalid positions: {', '.join(invalid)}")
    return positions


def normalize_region(raw_region: str) -> tuple[str, str]:
    requested = (raw_region or "CN").upper().strip() or "CN"
    normalized = REGION_ALIASES.get(requested, requested)
    if normalized not in SUPPORTED_REGIONS:
        normalized = "GLOBAL"
    return requested, normalized


def load_champions_from_runes_json(runes_path: Path) -> list[Champion]:
    if not runes_path.exists():
        return []

    payload = json.loads(runes_path.read_text(encoding="utf-8"))
    result = []
    for champion_id, champion_data in (payload.get("data") or {}).items():
        try:
            key = (champion_data or {}).get("key")
            if not key:
                continue
            result.append(Champion(id=int(champion_id), key=str(key)))
        except Exception:
            continue
    return result


def load_champions_from_frontend(frontend_champions_path: Path) -> list[Champion]:
    if not frontend_champions_path.exists():
        return []

    source = frontend_champions_path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"\{\s*id:\s*(\d+)\s*,\s*key:\s*'([^']+)'", re.MULTILINE)

    seen_ids: set[int] = set()
    champions: list[Champion] = []
    for match in pattern.finditer(source):
        champion_id = int(match.group(1))
        champion_key = match.group(2)
        if champion_id in seen_ids:
            continue
        seen_ids.add(champion_id)
        champions.append(Champion(id=champion_id, key=champion_key.lower()))

    return champions


def parse_manual_champions(raw_value: str) -> list[Champion]:
    if not raw_value:
        return []

    champions: list[Champion] = []
    for chunk in raw_value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise ValueError(f"invalid champion format: {chunk}, expected id:key")
        champion_id_str, champion_key = chunk.split(":", 1)
        champions.append(Champion(id=int(champion_id_str.strip()), key=champion_key.strip().lower()))
    return champions


def dedupe_champions(champions: list[Champion]) -> list[Champion]:
    unique: dict[int, Champion] = {}
    for champion in champions:
        unique[champion.id] = champion
    return [unique[champion_id] for champion_id in sorted(unique.keys())]


def load_champions(args: argparse.Namespace, project_root: Path) -> list[Champion]:
    champions: list[Champion] = []

    if args.champion_source == "manual":
        champions = parse_manual_champions(args.champions)
    elif args.champion_source == "frontend":
        source_file = Path(args.source_file) if args.source_file else project_root / "frontend" / "src" / "data" / "champions.js"
        champions = load_champions_from_frontend(source_file)
    elif args.champion_source == "runes-json":
        source_file = Path(args.source_file) if args.source_file else project_root / "data" / "runes.json"
        champions = load_champions_from_runes_json(source_file)
    elif args.champion_source == "auto":
        champions = load_champions_from_runes_json(project_root / "data" / "runes.json")
        if not champions:
            champions = load_champions_from_frontend(project_root / "frontend" / "src" / "data" / "champions.js")
    else:
        raise ValueError(f"unknown champion source: {args.champion_source}")

    champions = dedupe_champions(champions)
    if not champions:
        raise ValueError("no champions loaded, please check source or use --champion-source manual")
    return champions


def parse_position_data(api_payload: dict | None) -> dict | None:
    if not api_payload or "data" not in api_payload:
        return None

    data = api_payload["data"]
    return {
        "rune_pages": data.get("rune_pages", []),
        "summoner_spells": data.get("summoner_spells", []),
        "core_items": data.get("core_items", []),
        "boots": data.get("boots", []),
        "starter_items": data.get("starter_items", []),
        "skills": data.get("skills", []),
        "skill_masteries": data.get("skill_masteries", []),
        "counters": data.get("counters", []),
        "game_lengths": data.get("game_lengths", []),
        "trends": data.get("trends", {}),
    }


def build_api_url(region: str, champion_key: str, position: str) -> str:
    return f"https://lol-api-champion.op.gg/api/{region}/champions/ranked/{champion_key}/{position}"


def fetch_one(
    session: requests.Session,
    limiter: SharedRateLimiter,
    region: str,
    champion: Champion,
    position: str,
    timeout_seconds: int,
    max_attempts: int,
) -> dict | None:
    url = build_api_url(region=region, champion_key=champion.key, position=position)

    for attempt in range(1, max_attempts + 1):
        limiter.wait_turn()
        try:
            response = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout_seconds)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 404:
                return None
            if response.status_code == 429:
                time.sleep(min(6.0, 0.8 * attempt))
                continue
        except requests.RequestException:
            time.sleep(min(5.0, 0.5 * attempt))

    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch runes data from OP.GG API")
    parser.add_argument("--region", default="CN", help="OP.GG region, e.g. CN(=GLOBAL) / KR / NA / EUW")
    parser.add_argument("--positions", default=",".join(DEFAULT_POSITIONS), help="Comma-separated positions")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent worker count")
    parser.add_argument("--min-interval", type=float, default=0.2, help="Global min interval seconds between requests")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout seconds")
    parser.add_argument("--retries", type=int, default=3, help="HTTP retries for each request")
    parser.add_argument("--attempts", type=int, default=3, help="Max attempts per champion-position")
    parser.add_argument("--output", default="data/runes.json", help="Output json path")
    parser.add_argument("--version", default="", help="Data version label; default auto-generated")
    parser.add_argument(
        "--champion-source",
        default="auto",
        choices=["auto", "runes-json", "frontend", "manual"],
        help="Champion source mode",
    )
    parser.add_argument("--source-file", default="", help="Optional source file path for selected source mode")
    parser.add_argument("--champions", default="", help="Manual champions: id:key,id:key")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested_region, source_region = normalize_region(args.region)
    args.region = source_region
    start_time = time.time()

    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        positions = parse_positions(args.positions)
        champions = load_champions(args, project_root)
    except Exception as exc:
        print(f"[error] invalid arguments or champion source: {exc}")
        return 1

    worker_count = max(1, int(args.workers))
    limiter = SharedRateLimiter(args.min_interval)
    local_store = threading.local()

    result_data: dict[str, dict] = {
        str(champion.id): {
            "key": champion.key,
            "positions": {},
        }
        for champion in champions
    }

    stats = {
        "total": len(champions) * len(positions),
        "success": 0,
        "no_data": 0,
        "failed": 0,
    }
    stats_lock = threading.Lock()
    data_lock = threading.Lock()

    print("=" * 72)
    print("Rune Data Fetch - OP.GG Ranked API")
    print(f"region={requested_region} (source={source_region}) | champions={len(champions)} | positions={positions}")
    print(f"workers={worker_count} | min_interval={args.min_interval}s | timeout={args.timeout}s")
    print(f"output={output_path}")
    print("=" * 72)

    def get_session() -> requests.Session:
        session = getattr(local_store, "session", None)
        if session is None:
            session = create_retry_session(retries=max(0, int(args.retries)))
            local_store.session = session
        return session

    def task(champion: Champion, position: str):
        session = get_session()
        payload = fetch_one(
            session=session,
            limiter=limiter,
            region=args.region,
            champion=champion,
            position=position,
            timeout_seconds=max(1, int(args.timeout)),
            max_attempts=max(1, int(args.attempts)),
        )

        parsed = parse_position_data(payload)
        if parsed and parsed.get("rune_pages"):
            with data_lock:
                result_data[str(champion.id)]["positions"][position] = parsed
            with stats_lock:
                stats["success"] += 1
            return champion.key, position, "OK"

        if payload is None:
            with stats_lock:
                stats["failed"] += 1
            return champion.key, position, "FAIL"

        with stats_lock:
            stats["no_data"] += 1
        return champion.key, position, "NO_DATA"

    futures = []
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        for champion in champions:
            for position in positions:
                futures.append(executor.submit(task, champion, position))

        finished = 0
        for future in as_completed(futures):
            finished += 1
            champion_key, position, status = future.result()
            print(f"[{finished:>4}/{stats['total']}] {champion_key:<14} {position:<8} {status}")

    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now().astimezone()
    duration_seconds = round(time.time() - start_time, 2)

    output_payload = {
        "version": args.version or utc_now.strftime("%Y.%m.%d"),
        "updateTime": local_now.strftime("%Y-%m-%d %H:%M:%S"),
        "meta": {
            "generated_at_utc": utc_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "region": requested_region,
            "source_region": source_region,
            "positions": positions,
            "workers": worker_count,
            "min_interval_seconds": args.min_interval,
            "duration_seconds": duration_seconds,
            "champion_source": args.champion_source,
            "stats": stats,
        },
        "data": result_data,
    }

    output_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 72)
    print(
        "Done | "
        f"success={stats['success']} "
        f"no_data={stats['no_data']} "
        f"failed={stats['failed']} "
        f"total={stats['total']} "
        f"rate={((stats['success'] / stats['total']) * 100 if stats['total'] else 0):.1f}%"
    )
    print(f"Saved to: {output_path}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

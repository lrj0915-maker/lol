"""符文抓取测试脚本（安全输出到 data/runes.test.json）。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


TEST_CHAMPIONS = [
    (157, "yasuo"),
    (238, "zed"),
    (55, "katarina"),
    (64, "leesin"),
    (81, "ezreal"),
]


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    fetch_script = project_root / "scripts" / "fetch_runes.py"
    output_file = project_root / "data" / "runes.test.json"

    champion_arg = ",".join(f"{champion_id}:{champion_key}" for champion_id, champion_key in TEST_CHAMPIONS)

    command = [
        sys.executable,
        str(fetch_script),
        "--champion-source",
        "manual",
        "--champions",
        champion_arg,
        "--positions",
        "TOP,JUNGLE,MID,ADC,SUPPORT",
        "--workers",
        "3",
        "--min-interval",
        "0.2",
        "--attempts",
        "2",
        "--retries",
        "2",
        "--output",
        str(output_file),
    ]

    print("[test] Running:")
    print(" ".join(command))

    completed = subprocess.run(command, cwd=str(project_root), check=False)
    if completed.returncode != 0:
        print(f"[test] failed with code {completed.returncode}")
        return completed.returncode

    if not output_file.exists():
        print("[test] output file missing")
        return 1

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    stats = (payload.get("meta") or {}).get("stats") or {}
    print(f"[test] done. output={output_file}")
    print(f"[test] stats={stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


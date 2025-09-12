import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(f"[main] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if res.returncode != 0:
        raise SystemExit(res.returncode)


def ensure_dirs() -> None:
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_dirs()
    # Use current interpreter to avoid env mismatch
    py = sys.executable
    run([py, "scripts/get_stock_price.py"])
    run([py, "scripts/update_all.py"])


if __name__ == "__main__":
    main()


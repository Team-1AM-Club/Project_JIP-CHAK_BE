from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import AsyncSessionLocal
from scripts.seeders.congestion import seed_congestion
from scripts.seeders.flood import seed_flood
from scripts.seeders.medical import seed_medical
from scripts.seeders.noise import seed_noise
from scripts.seeders.security import seed_security


DEFAULT_DATA_DIR = Path(os.getenv("DATA_DIR", "data"))


async def run(data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        results: dict[str, int] = {}
        for seeder in (seed_security, seed_flood, seed_noise, seed_medical, seed_congestion):
            results.update(await seeder(session, data_dir, replace=replace))
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed preprocessed reference data into ref_* tables.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--replace", action="store_true", help="Delete existing ref_* rows before inserting.")
    args = parser.parse_args()

    results = asyncio.run(run(args.data_dir, replace=args.replace))
    for table_name, inserted in sorted(results.items()):
        print(f"{table_name}: inserted={inserted}")


if __name__ == "__main__":
    main()

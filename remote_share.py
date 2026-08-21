"""How remote is this role, really — per city, on organic listings only.

Indeed writes the flag several ways ("Remote", "Hybrid work", "Remote in Austin, TX"),
so the classifier below is deliberately simple and reports what it saw.

    python3 remote_share.py "software engineer" --cities cities.txt
"""
from __future__ import annotations

import argparse
import pathlib
from collections import Counter

from indeed import collect, organic

DEFAULT_CITIES = ["Austin, TX", "New York, NY", "San Francisco, CA", "Boston, MA", "Remote"]


def classify(row: dict) -> str:
    label = f"{row.get('remote') or ''} {row.get('location') or ''}".lower()
    if "hybrid" in label:
        return "hybrid"
    if "remote" in label:
        return "remote"
    return "onsite"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--cities", type=pathlib.Path, default=None)
    ap.add_argument("--country", default="us")
    ap.add_argument("--max", type=int, default=150)
    args = ap.parse_args()

    cities = ([ln.strip() for ln in args.cities.read_text(encoding="utf-8").splitlines() if ln.strip()]
              if args.cities else DEFAULT_CITIES)

    print(f"{args.query}\n")
    print(f"{'city':<22}{'listings':>9}{'remote':>9}{'hybrid':>9}{'onsite':>9}")
    for city in cities:
        try:
            rows = organic(collect("indeed_jobs", query=args.query, location=city,
                                   country=args.country, max_results=args.max))
        except RuntimeError as exc:
            print(f"{city:<22} !! {exc}")
            continue
        counts = Counter(classify(r) for r in rows)
        total = sum(counts.values()) or 1
        print(f"{city:<22}{total:>9}"
              f"{100 * counts['remote'] // total:>8}%"
              f"{100 * counts['hybrid'] // total:>8}%"
              f"{100 * counts['onsite'] // total:>8}%")


if __name__ == "__main__":
    main()

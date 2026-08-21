"""One role, many cities — median annualised pay and the disclosure rate.

The disclosure column matters as much as the medians: a city where 15% of
listings show pay gives you a much shakier median than one where 80% do.

    python3 market_rates.py "registered nurse" --cities cities.txt --max 150
"""
from __future__ import annotations

import argparse
import pathlib
import statistics
from concurrent.futures import ThreadPoolExecutor

from indeed import annualise, collect, organic

DEFAULT_CITIES = ["New York, NY", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
                  "Denver, CO", "Seattle, WA", "Atlanta, GA", "Miami, FL"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--cities", type=pathlib.Path, default=None)
    ap.add_argument("--country", default="us")
    ap.add_argument("--max", type=int, default=150)
    args = ap.parse_args()

    cities = ([ln.strip() for ln in args.cities.read_text(encoding="utf-8").splitlines() if ln.strip()]
              if args.cities else DEFAULT_CITIES)

    def probe(city: str):
        try:
            rows = organic(collect("indeed_jobs", query=args.query, location=city,
                                   country=args.country, max_results=args.max))
        except RuntimeError as exc:
            return city, None, str(exc)
        return city, rows, None

    print(f"{args.query} — {len(cities)} markets\n")
    print(f"{'city':<22}{'listings':>9}{'w/ pay':>8}{'p25':>12}{'median':>12}{'p75':>12}")

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for city, rows, error in pool.map(probe, cities):
            if error:
                print(f"{city:<22} !! {error}")
                continue
            pay = sorted(v for v in
                         (annualise(r.get("salary_min"), r.get("salary_max"), r.get("salary_period"))
                          for r in rows) if v)
            if len(pay) < 4:
                print(f"{city:<22}{len(rows):>9}{len(pay):>8}      too few disclosed")
                continue
            q = statistics.quantiles(pay, n=4)
            results.append((city, statistics.median(pay)))
            print(f"{city:<22}{len(rows):>9}{len(pay):>8}"
                  f"{q[0]:>12,.0f}{q[1]:>12,.0f}{q[2]:>12,.0f}")

    if len(results) > 1:
        results.sort(key=lambda t: -t[1])
        top, bottom = results[0], results[-1]
        print(f"\nspread: {top[0]} ${top[1]:,.0f} vs {bottom[0]} ${bottom[1]:,.0f} "
              f"({100 * (top[1] / bottom[1] - 1):.0f}% higher)")


if __name__ == "__main__":
    main()

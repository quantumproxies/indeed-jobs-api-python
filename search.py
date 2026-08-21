"""One Indeed search → CSV, with a summary that separates ads from organic rows.

    python3 search.py "warehouse associate" "Columbus, OH" --days 7 --max 200
"""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import Counter

from indeed import annualise, collect, organic

FIELDS = ["rank", "title", "company", "location", "remote", "salary", "salary_min",
          "salary_max", "salary_period", "posted", "company_rating", "company_reviews",
          "sponsored", "job_key", "link"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("location")
    ap.add_argument("--country", default="us")
    ap.add_argument("--days", type=int, default=None, help="posted within N days (1-30)")
    ap.add_argument("--max", type=int, default=100)
    ap.add_argument("--out", default="jobs.csv")
    args = ap.parse_args()

    rows = collect("indeed_jobs", query=args.query, location=args.location,
                   country=args.country, posted_within_days=args.days, max_results=args.max)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    real = organic(rows)
    pay = [v for v in (annualise(r.get("salary_min"), r.get("salary_max"), r.get("salary_period"))
                       for r in real) if v]

    print(f"{len(rows)} listings ({len(rows) - len(real)} sponsored) → {args.out}")
    if pay:
        print(f"pay disclosed on {len(pay)}/{len(real)} organic rows — "
              f"median ${statistics.median(pay):,.0f}/yr")
    remote = sum(1 for r in real if r.get("remote"))
    print(f"remote or hybrid: {remote}/{len(real)}\n")

    print("top employers (organic only)")
    for company, n in Counter(r.get("company") for r in real).most_common(12):
        print(f"  {n:>3}  {company}")


if __name__ == "__main__":
    main()

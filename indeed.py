"""Client and row helpers for the Indeed jobs collector."""
from __future__ import annotations

import os
import re
import time
from typing import Any

import requests

BASE = "https://api.quanticdata.io/v1"
_s = requests.Session()

# Assumptions, stated once and used everywhere.
HOURS_PER_YEAR = 2080
DAYS_PER_YEAR = 260
WEEKS_PER_YEAR = 52
MONTHS_PER_YEAR = 12
PERIOD_FACTOR = {
    "hour": HOURS_PER_YEAR,
    "day": DAYS_PER_YEAR,
    "week": WEEKS_PER_YEAR,
    "month": MONTHS_PER_YEAR,
    "year": 1,
}


def _h() -> dict[str, str]:
    key = os.environ.get("QUANTICDATA_API_KEY")
    if not key:
        raise SystemExit("set QUANTICDATA_API_KEY — https://app.quanticdata.io/register")
    return {"Authorization": f"Bearer {key}"}


def collect(slug: str, **input_: Any) -> list[dict]:
    payload = {k: v for k, v in input_.items() if v not in (None, False, "")}
    r = _s.post(f"{BASE}/scraper/collectors/{slug}/run", json=payload, headers=_h(), timeout=300)
    body = r.json()
    if body.get("type") == "error" or not r.ok:
        raise RuntimeError(f"{slug} ({r.status_code}): {body.get('message')}")

    run = body.get("payload", {})
    while run.get("status") in ("queued", "running"):
        time.sleep(3)
        run = _s.get(f"{BASE}/scraper/collectors/runs/{run['run_id']}",
                     headers=_h(), timeout=60).json().get("payload", {})
    return run.get("results") or []


def annualise(low: float | None, high: float | None, period: str | None) -> float | None:
    """Mid-point of the range, converted to a yearly figure. None when unusable."""
    values = [v for v in (low, high) if isinstance(v, (int, float)) and v > 0]
    factor = PERIOD_FACTOR.get((period or "").lower())
    if not values or not factor:
        return None
    return (sum(values) / len(values)) * factor


def company_key(name: str | None) -> str:
    """'Acme Logistics, Inc.' and 'ACME Logistics Inc' collapse to the same key."""
    cleaned = re.sub(r"\b(inc|llc|ltd|corp|co|gmbh|s\.?p\.?a|s\.?r\.?l)\b\.?", " ",
                     (name or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", cleaned).strip()


def organic(rows: list[dict]) -> list[dict]:
    """Drop the paid placements — they are ads, not market signal."""
    return [r for r in rows if not r.get("sponsored")]

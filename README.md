# Indeed jobs API in Python — parsed salary ranges, remote flags, company ratings

The [`indeed_jobs` collector](https://quanticdata.io/collectors/indeed-jobs-api/) returns Indeed
listings already parsed: title, company, location, remote label, the salary line **plus
`salary_min` / `salary_max` / `salary_period` as numbers**, job types, posted label, snippet,
company rating and review count, sponsored flag and link.

$0.001 per job, up to 300 per run. The parsed salary fields are the reason to reach for this
one over a generic SERP scrape — Indeed writes salary six different ways and the collector
normalises all of them.

```bash
pip install requests
export QUANTICDATA_API_KEY=qd_live_your_key_here

python3 search.py "warehouse associate" "Columbus, OH" --days 7 --out jobs.csv
python3 market_rates.py "registered nurse" --cities cities.txt
python3 remote_share.py "software engineer" --cities cities.txt
```

## Files

| File | What it does |
|---|---|
| [`indeed.py`](indeed.py) | collector client + row helpers (annualise a salary, normalise a company name) |
| [`search.py`](search.py) | one search → CSV + summary |
| [`market_rates.py`](market_rates.py) | the same role across cities, compared on median annualised pay |
| [`remote_share.py`](remote_share.py) | how much of a role's market is remote, per city |

## Output row

```jsonc
{ "rank": 1, "job_key": "a1b2c3…", "title": "Warehouse Associate",
  "company": "Acme Logistics", "location": "Columbus, OH 43219",
  "remote": "Hybrid work", "salary": "$18 - $22 an hour",
  "salary_min": 18, "salary_max": 22, "salary_period": "hour",
  "job_types": ["Full-time"], "posted": "3 days ago",
  "snippet": "…", "company_rating": 3.4, "company_reviews": 1820,
  "sponsored": false, "link": "https://www.indeed.com/viewjob?jk=a1b2c3…" }
```

## Annualising, correctly

`salary_period` is `hour`, `day`, `week`, `month` or `year`. Comparing a $22/hour role with a
$95,000/year role means converting first, and the conversion has assumptions — `indeed.py` uses
2,080 hours, 260 days and 52 weeks a year, and says so out loud rather than hiding it:

```python
from indeed import annualise
annualise(18, 22, "hour")     # -> 41_600, mid-point of the range annualised
```

Two caveats worth repeating in any report you build on this:

- **Sponsored rows are ads.** They count toward `max_results` and skew a "top employers" list.
  Filter on `sponsored` before ranking anything.
- **Only some listings disclose pay.** The disclosure rate is itself the interesting number in
  markets with pay-transparency laws, and `market_rates.py` prints it alongside the medians.

## Related

- [Indeed jobs API](https://quanticdata.io/collectors/indeed-jobs-api/) · [LinkedIn jobs API](https://quanticdata.io/collectors/linkedin-jobs-api/) · [Google Jobs API](https://quanticdata.io/collectors/google-jobs-api/)
- [Scrape job postings](https://quanticdata.io/scrape-job-postings/) · [All collectors](https://quanticdata.io/collectors/)
- [Is web scraping legal in the US?](https://quanticdata.io/blog/is-web-scraping-legal-in-us/)

MIT licensed.

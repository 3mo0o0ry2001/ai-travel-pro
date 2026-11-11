"""HTTP smoke load for public endpoints; no flight-provider requests are made."""

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen


def run_load(base_url, requests, concurrency):
    def measure(index):
        started = time.perf_counter()
        path = "/api/session" if index % 2 else "/"
        with urlopen(base_url.rstrip("/") + path, timeout=15) as response:
            response.read()
            return (time.perf_counter() - started) * 1000, response.status

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        observations = list(pool.map(measure, range(requests)))
    timings = sorted(duration for duration, _ in observations)
    return {
        "requests": requests,
        "concurrency": concurrency,
        "failures": sum(status != 200 for _, status in observations),
        "p50_ms": round(statistics.median(timings), 2),
        "p95_ms": round(timings[min(len(timings) - 1, int(len(timings) * 0.95))], 2),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "scope": "Public home and session only; excludes flight search and email",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.requests <= 10000 or not 1 <= args.concurrency <= 100:
        parser.error("Use 1–10000 requests and 1–100 concurrent clients")
    print(json.dumps(run_load(args.base_url, args.requests, args.concurrency), indent=2))

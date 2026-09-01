#!/usr/bin/env python3
"""Query gpu-prices local cache. Usage: query.py [--json] <command> [filter]"""

import json
import sys
import os
import datetime
from pathlib import Path

CACHE_FILE = Path(__file__).parent / "cache" / "data.json"
LIVE_URL = "https://gputable.dev/data.json"

def load_data():
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    # Fallback: fetch live
    import urllib.request
    with urllib.request.urlopen(LIVE_URL, timeout=10) as r:
        return json.load(r)

def cache_age():
    if not CACHE_FILE.exists():
        return None
    mtime = datetime.datetime.fromtimestamp(CACHE_FILE.stat().st_mtime, tz=datetime.timezone.utc)
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return now - mtime

def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    if as_json:
        args = [a for a in args if a != "--json"]

    cmd = args[0] if args else "summary"
    filt = args[1].lower() if len(args) > 1 else ""
    spot_only = "--spot" in args
    if spot_only:
        filt = args[1].lower() if len(args) > 1 and not args[1].startswith("--") else ""

    if cmd == "cache-age":
        age = cache_age()
        if age is None:
            print("No cache file — run fetch-cache.sh first")
        else:
            h, m = divmod(int(age.total_seconds()), 3600)
            m = m // 60
            print(f"Cache age: {h}h {m}m (generated_at in file may differ from mtime)")
        return

    data = load_data()
    rows = data.get("data", [])
    generated_at = data.get("generated_at", "unknown")

    if cmd == "gpus":
        gpus = sorted(set(r["gpu"] for r in rows))
        if as_json:
            print(json.dumps(gpus, indent=2))
        else:
            print(f"GPUs tracked ({len(gpus)}) as of {generated_at}:")
            for g in gpus:
                print(f"  {g}")
        return

    if cmd == "prices":
        if not filt:
            print("Usage: query.py prices <gpu_model>")
            sys.exit(1)
        matched = [r for r in rows if filt in r["gpu"].lower()]
        if not matched:
            print(f"No rows matching '{filt}'")
            return
        matched.sort(key=lambda r: r["price_per_hour_usd"])
        if as_json:
            print(json.dumps(matched, indent=2))
            return
        gpu_name = matched[0]["gpu"]
        print(f"{gpu_name} prices ({len(matched)} offers) as of {generated_at}:")
        print(f"  {'Provider':<20} {'$/hr':>7}  {'Type':<12} {'Avail':<6}  Source")
        for r in matched:
            avail = "yes" if r.get("available") else ("no" if r.get("available") is False else "?")
            print(f"  {r['provider']:<20} ${r['price_per_hour_usd']:>6.4f}  {r['pricing_type']:<12} {avail:<6}  {r['source_url']}")
        return

    if cmd == "cheapest":
        pricing_types = ["spot"] if spot_only else ["on_demand", "spot", "reserved"]
        matched = [r for r in rows if r.get("available") and r["pricing_type"] in pricing_types]
        if filt:
            matched = [r for r in matched if filt in r["gpu"].lower()]
        if not matched:
            print(f"No available rows matching filter '{filt}'")
            return
        matched.sort(key=lambda r: r["price_per_hour_usd"])
        top = matched[:20]
        if as_json:
            print(json.dumps(top, indent=2))
            return
        label = f"'{filt}' " if filt else ""
        print(f"Cheapest {label}GPUs (available now) as of {generated_at}:")
        print(f"  {'GPU':<28} {'Provider':<20} {'$/hr':>7}  {'Type':<10}")
        for r in top:
            print(f"  {r['gpu']:<28} {r['provider']:<20} ${r['price_per_hour_usd']:>6.4f}  {r['pricing_type']:<10}")
        return

    if cmd == "summary":
        # Cheapest available price per GPU model
        by_gpu = {}
        for r in rows:
            if r.get("available"):
                gpu = r["gpu"]
                if gpu not in by_gpu or r["price_per_hour_usd"] < by_gpu[gpu]["price_per_hour_usd"]:
                    by_gpu[gpu] = r
        if as_json:
            print(json.dumps(list(by_gpu.values()), indent=2))
            return
        sorted_gpus = sorted(by_gpu.values(), key=lambda r: r["price_per_hour_usd"])
        print(f"Cheapest available price per GPU as of {generated_at}:")
        print(f"  {'GPU':<28} {'$/hr':>7}  {'Provider':<20} {'Type'}")
        for r in sorted_gpus:
            print(f"  {r['gpu']:<28} ${r['price_per_hour_usd']:>6.4f}  {r['provider']:<20} {r['pricing_type']}")
        return

    print(f"Unknown command: {cmd}")
    print("Commands: gpus, prices <model>, cheapest [model], summary, cache-age")
    sys.exit(1)

if __name__ == "__main__":
    main()

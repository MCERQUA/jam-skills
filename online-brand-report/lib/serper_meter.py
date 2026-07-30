"""serper_meter.py — best-effort Serper credit usage meter.

Serper has NO balance API (a response's `credits` field is the COST of that call;
`x-ratelimit-remaining` is the per-second rate limit, not the account balance). So remaining
credits can only be ESTIMATED: seeded top-up minus summed usage. This module is the usage half.

record(credits) appends one line to the usage log. It is deliberately BULLETPROOF — any failure
(disk, perms, bad input) is swallowed, because metering must NEVER break a paid report mid-run.
The balance-poller reads seed top-up from serper-credits.json and sums this log since topup_at.
"""
from __future__ import annotations

import os
import time

USAGE_LOG = os.environ.get("SERPER_USAGE_LOG", "/mnt/system/monitoring/serper-usage.log")


def record(credits, endpoint: str = "") -> None:
    """Append '<epoch> <iso> <credits> <endpoint>' to the usage log. Never raises."""
    try:
        c = int(credits or 0)
        if c <= 0:
            return
        now = time.time()
        line = f"{now:.0f}\t{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}\t{c}\t{endpoint}\n"
        os.makedirs(os.path.dirname(USAGE_LOG), exist_ok=True)
        # append mode is atomic enough for short lines across processes on local fs
        with open(USAGE_LOG, "a") as f:
            f.write(line)
    except Exception:
        pass  # metering must never break the report

#!/usr/bin/env python3
"""
Retrace HTTP demo (stable endpoints, real network)

What it shows:
- A controlled retry/backoff path using a guaranteed 503 then a success.
- An optional bug to replay into (ZeroDivisionError).
- Captures non-determinism (random roll) so replay shows frozen randomness.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

API_BASE = "https://jsonplaceholder.typicode.com"
HTTPSTAT_503 = "https://httpstat.us/503"


@dataclass
class Summary:
    correlation_id: str
    user_name: str
    post_title: str
    todo_title: str
    retry_status: int
    retry_attempts: int
    random_roll: float
    elapsed_ms: float


def fetch_json(session: requests.Session, url: str, *, timeout: float = 10.0) -> Dict[str, Any]:
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def retry_with_forced_failure(session: requests.Session, *, timeout: float = 10.0, backoff: float = 0.3) -> tuple[int, int]:
    """
    Retry path that is deterministic but real-network:
    - First attempt: call httpstat.us/503 (always 503) to force a failure.
    - Second attempt: call jsonplaceholder/todos/2 (stable 200).
    """
    attempts = 0

    # Attempt 1: guaranteed 503
    attempts += 1
    try:
        r1 = session.get(HTTPSTAT_503, timeout=timeout)
        r1.raise_for_status()
    except Exception:
        time.sleep(backoff * attempts)
    else:
        return r1.status_code, attempts 

    # Attempt 2: stable success
    attempts += 1
    r2 = session.get(f"{API_BASE}/todos/2", timeout=timeout)
    status = r2.status_code
    if status >= 500:
        raise requests.HTTPError(f"server error {status}", response=r2)
    return status, attempts


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrace HTTP demo")
    parser.add_argument("--trigger-bug", action="store_true", help="Trigger an intentional bug to replay into")
    args = parser.parse_args()

    corr = str(uuid.uuid4())[:8]
    print(f"[demo] correlation_id={corr}")

    session = requests.Session()
    session.headers.update({"User-Agent": "retrace-http-demo/1.0", "X-Demo-Correlation-Id": corr})

    start = time.perf_counter() * 1000.0

    user = fetch_json(session, f"{API_BASE}/users/1")
    post = fetch_json(session, f"{API_BASE}/posts/1")
    todo = fetch_json(session, f"{API_BASE}/todos/1")

    user_display = "user1"  
    print(f"[demo] user: {user_display!r}")
    print(f"[demo] post title: {post.get('title')!r}")
    print(f"[demo] todo title: {todo.get('title')!r}, completed={todo.get('completed')}")

    retry_status, retry_attempts = retry_with_forced_failure(session, timeout=10.0, backoff=0.4)
    print(f"[demo] forced-retry final_status={retry_status} attempts={retry_attempts}")

    roll = random.random()

    if args.trigger_bug:
        print("[demo] triggering intentional bug (ZeroDivisionError)")
        _ = 1 / 0

    elapsed = time.perf_counter() * 1000.0 - start
    summary = Summary(
        correlation_id=corr,
        user_name=user_display,
        post_title=str(post.get("title")),
        todo_title=str(todo.get("title")),
        retry_status=retry_status,
        retry_attempts=retry_attempts,
        random_roll=roll,
        elapsed_ms=elapsed,
    )

    print("[demo] summary:")
    print(json.dumps(summary.__dict__, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[demo] crashed: {type(e).__name__}: {e}", file=sys.stderr)
        raise


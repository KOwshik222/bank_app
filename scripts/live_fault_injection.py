"""
Live Banking Traffic & Real Fault Injection Suite
=================================================
Sends high-concurrency requests to the live banking endpoints to generate
real application logs, metrics, and error spikes.

Usage:
    python scripts/live_fault_injection.py --mode normal --count 50
    python scripts/live_fault_injection.py --mode error_spike --count 50
    python scripts/live_fault_injection.py --mode pool_exhaustion --count 100
"""

import argparse
import asyncio
import random
import sys
import time
from typing import Any
import httpx

BASE_URL = "http://localhost:8000"


async def check_health(client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"{BASE_URL}/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


async def get_active_accounts(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Retrieve existing accounts to use for real transfers."""
    try:
        r = await client.get(f"{BASE_URL}/api/accounts/?limit=10", timeout=3.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


async def send_transfer(
    client: httpx.AsyncClient,
    source_acc: str,
    dest_acc: str,
    amount: float,
    desc: str = "Live transfer",
    payment_method: str = "INTERNAL",
) -> tuple[int, str]:
    payload = {
        "source_account_id": source_acc,
        "destination_account_id": dest_acc,
        "amount": amount,
        "currency": "USD",
        "description": desc,
        "payment_method": payment_method,
    }
    try:
        r = await client.post(f"{BASE_URL}/api/payments/", json=payload, timeout=5.0)
        return r.status_code, r.text[:120]
    except httpx.TimeoutException:
        return 504, "ClientTimeout"
    except Exception as e:
        return 500, type(e).__name__


async def run_traffic(mode: str = "normal", count: int = 50, concurrency: int = 10):
    print(f"\n========================================================")
    print(f"  BANKOPS LIVE TRAFFIC GENERATOR: [{mode.upper()}]")
    print(f"  Target: {BASE_URL} | Total: {count} | Concurrency: {concurrency}")
    print(f"========================================================")

    async with httpx.AsyncClient() as client:
        is_up = await check_health(client)
        if not is_up:
            print(f"[!] ERROR: Banking backend at {BASE_URL} is not responding!")
            print(f"    Please start the server: python -m uvicorn app.main:app --port 8000")
            sys.exit(1)

        accounts = await get_active_accounts(client)
        acc_ids = [a.get("account_number") or a.get("id") for a in accounts if a.get("id")]
        if len(acc_ids) < 2:
            acc_ids = ["ACC-10000000", "ACC-10000001", "ACC-10000002"]

        print(f"[*] Discovered {len(acc_ids)} active account targets: {acc_ids[:3]}")
        print(f"[*] Generating live network traffic...")

        sem = asyncio.Semaphore(concurrency)

        async def worker(idx: int):
            async with sem:
                if mode == "normal":
                    src = random.choice(acc_ids)
                    dst = random.choice([a for a in acc_ids if a != src] or acc_ids)
                    amt = round(random.uniform(5.0, 50.0), 2)
                    return await send_transfer(client, src, dst, amt, f"Normal txn #{idx}", payment_method="INTERNAL")

                elif mode == "error_spike":
                    fault_type = idx % 3
                    if fault_type == 0:
                        # Unsupported payment method triggers ValueError in service
                        src = random.choice(acc_ids)
                        dst = random.choice([a for a in acc_ids if a != src] or acc_ids)
                        return await send_transfer(client, src, dst, 50.0, f"FAULT_METHOD #{idx}", payment_method="INVALID_CRYPTO")
                    elif fault_type == 1:
                        # Excessive overdraft amount
                        src = random.choice(acc_ids)
                        dst = random.choice([a for a in acc_ids if a != src] or acc_ids)
                        return await send_transfer(client, src, dst, 99999999.00, f"FAULT_OVERDRAFT #{idx}")
                    else:
                        # Non-existent source account
                        src = f"NONEXISTENT-{random.randint(90000, 99999)}"
                        dst = random.choice(acc_ids)
                        return await send_transfer(client, src, dst, 25.0, f"FAULT_SRC #{idx}")

                elif mode == "pool_exhaustion":
                    src = random.choice(acc_ids)
                    dst = random.choice([a for a in acc_ids if a != src] or acc_ids)
                    amt = 1.00
                    return await send_transfer(client, src, dst, amt, f"POOL_STRESS #{idx}", payment_method="INTERNAL")

        start_time = time.time()
        tasks = [worker(i) for i in range(count)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        status_counts: dict[int, int] = {}
        for status, _ in results:
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n[+] Live Traffic Completed in {elapsed:.2f}s ({count / elapsed:.1f} req/s)")
        print(f"    Status Code Breakdown:")
        for status, cnt in sorted(status_counts.items()):
            symbol = " [OK]" if status in (200, 201) else " [ERR]"
            print(f"      HTTP {status}{symbol}: {cnt} requests ({cnt / count * 100:.1f}%)")
        print(f"========================================================\n")


def main():
    parser = argparse.ArgumentParser(description="BankOps Live Traffic & Fault Injector")
    parser.add_argument("--mode", choices=["normal", "error_spike", "pool_exhaustion"], default="normal")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    asyncio.run(run_traffic(mode=args.mode, count=args.count, concurrency=args.concurrency))


if __name__ == "__main__":
    main()

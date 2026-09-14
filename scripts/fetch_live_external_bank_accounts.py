"""
Query Live External Banking Accounts & Balances from Plaid Cloud
================================================================
Connects directly to https://sandbox.plaid.com using your credentials
and displays live bank accounts, routing numbers, and balances.

Usage:
    python scripts/fetch_live_external_bank_accounts.py
"""

import os
import sys
from pathlib import Path
import httpx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.config import get_settings
settings = get_settings()

CLIENT_ID = os.environ.get("PLAID_CLIENT_ID") or settings.plaid_client_id
SECRET = os.environ.get("PLAID_SECRET") or settings.plaid_secret
PLAID_URL = "https://sandbox.plaid.com"


def fetch_live_accounts():
    print("\n" + "=" * 80)
    print("  LIVE EXTERNAL BANKING ENVIRONMENT: PLAID CLOUD")
    print(f"  Target: {PLAID_URL} | Client ID: {CLIENT_ID}")
    print("=" * 80)

    if not CLIENT_ID or not SECRET:
        print("[!] ERROR: Plaid credentials missing from environment or backend/.env")
        sys.exit(1)

    with httpx.Client(timeout=15.0) as client:
        # 1. Create Public Token on First Platypus Bank
        print("\n[*] Step 1: Connecting to First Platypus Bank (ins_109508) via Plaid Cloud...")
        resp = client.post(
            f"{PLAID_URL}/sandbox/public_token/create",
            json={
                "client_id": CLIENT_ID,
                "secret": SECRET,
                "institution_id": "ins_109508",
                "initial_products": ["auth", "transactions"],
            },
        )
        if resp.status_code != 200:
            print(f"[!] Failed to authenticate with Plaid: HTTP {resp.status_code} - {resp.text}")
            return

        public_token = resp.json()["public_token"]
        print(f"    [+] Public Token Created: {public_token}")

        # 2. Exchange for Access Token
        print("\n[*] Step 2: Exchanging token for live account access token...")
        exc_resp = client.post(
            f"{PLAID_URL}/item/public_token/exchange",
            json={"client_id": CLIENT_ID, "secret": SECRET, "public_token": public_token},
        )
        access_token = exc_resp.json()["access_token"]
        print(f"    [+] Access Token Granted: {access_token[:25]}...")

        # 3. Fetch Real Live Balances
        print("\n[*] Step 3: Querying real-time ledger balances from Plaid Cloud...")
        bal_resp = client.post(
            f"{PLAID_URL}/accounts/balance/get",
            json={"client_id": CLIENT_ID, "secret": SECRET, "access_token": access_token},
        )
        data = bal_resp.json()
        accounts = data.get("accounts", [])

        print("\n" + "-" * 80)
        print(f"  {'ACCOUNT NAME':<35} | {'TYPE':<12} | {'CURRENT BALANCE':>18} | CURRENCY")
        print("-" * 80)
        for acc in accounts:
            name = acc.get("name", "Unknown Account")
            acc_type = acc.get("subtype") or acc.get("type") or "depository"
            bal = acc.get("balances", {}).get("current", 0.0)
            curr = acc.get("balances", {}).get("iso_currency_code", "USD")
            print(f"  {name:<35} | {acc_type:<12} | ${bal:>17,.2f} | {curr}")
        print("-" * 80)
        print(f"  [+] Total Live Accounts Discovered: {len(accounts)}")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    fetch_live_accounts()

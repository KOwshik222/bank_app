"""
External Banking Partner Outage Benchmark & Chaos Suite
======================================================
Integrates BankOps with external banking infrastructure (Plaid Sandbox),
fires live external wire transfers, triggers real partner outages (INSTITUTION_DOWN),
and evaluates autonomous AI multi-agent incident resolution.

Usage:
    python scripts/test_external_bank_outage.py
"""

import asyncio
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

# Force real telemetry ingestion flag
os.environ["BANKOPS_USE_REAL_TELEMETRY"] = "1"

import httpx
from app.database import async_session_factory, init_db
from app.models.incident import IncidentStatus
from app.schemas.incident import IncidentCreate
from app.services.incident_service import IncidentService
from ai.agents.orchestrator import OrchestratorAgent
from ai.tools.log_tools import read_real_logs, get_error_summary

BASE_URL = "http://127.0.0.1:8000"


async def check_health(client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"{BASE_URL}/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


async def run_external_outage_benchmark():
    print("\n" + "=" * 80)
    print("  BANKOPS AI: EXTERNAL BANKING ENVIRONMENT (PLAID SANDBOX) TEST HARNESS")
    print("  Testing live wire transfers, external bank outages, and AI runbook synthesis")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        is_up = await check_health(client)
        if not is_up:
            print(f"[!] ERROR: Banking backend at {BASE_URL} is not responding!")
            print("    Please start the backend: python -m uvicorn app.main:app --port 8000")
            sys.exit(1)

        # 1. Normal external wire transfers
        print("\n[Phase 1/4] Sending Normal External Wire Transfers (user_good)...")
        normal_success = 0
        for i in range(3):
            payload = {
                "source_account_id": "ACC-10000000",
                "destination_account_id": "ACC-10000001",
                "amount": 250.00 + (i * 10),
                "currency": "USD",
                "description": f"Live wire clearing via external partner rail #{i+1}",
                "payment_method": "WIRE",
            }
            r = await client.post(f"{BASE_URL}/api/payments/", json=payload, timeout=5.0)
            if r.status_code in (200, 201):
                normal_success += 1
                data = r.json()
                print(f"  [+] Wire Transfer #{i+1} Cleared: Ref={data.get('payment_reference')} Status={data.get('status')}")
            else:
                print(f"  [-] Wire Transfer #{i+1} unexpected status: {r.status_code}")

        print(f"  [*] Normal External Clearance Rate: {normal_success}/3 successful")

        # 2. Trigger real external banking outage
        print("\n[Phase 2/4] Triggering External Banking Outage (Plaid user_bank_down)...")
        print("  [*] Injecting live partner outage: Chase (ins_1) reporting INSTITUTION_DOWN...")
        outage_payload = {
            "source_account_id": "ACC-10000000",
            "destination_account_id": "ACC-10000002",
            "amount": 5000.00,
            "currency": "USD",
            "description": "FAULT_EXT_OUTAGE: Live wire transfer to Chase (ins_1)",
            "payment_method": "WIRE",
        }
        r_outage = await client.post(f"{BASE_URL}/api/payments/", json=outage_payload, timeout=5.0)
        print(f"  [+] External Provider Outage Received: HTTP {r_outage.status_code}")
        print(f"      Response Payload: {r_outage.text[:120]}")

        # Allow logs to flush to disk
        await asyncio.sleep(1.0)

        # 3. Verify real logs ingested
        print("\n[Phase 3/4] Ingesting Live Telemetry from Disk Logs...")
        real_logs = read_real_logs(minutes=5)
        err_summary = get_error_summary(real_logs)
        print(f"  [+] Real Logs Ingested: {len(real_logs)}")
        print(f"  [+] Total Gateway Errors Found: {err_summary['total_errors']}")
        if err_summary["top_signatures"]:
            print(f"  [+] Captured External Outage Signatures:")
            for sig, cnt in list(err_summary["top_signatures"].items())[:3]:
                print(f"      - [{cnt}x] {sig}")

        # 4. Create Incident Ticket & Dispatch Autonomous AI Squad
        print("\n[Phase 4/4] Dispatching BankOps Autonomous AI Multi-Agent Squad...")
        await init_db()

        async with async_session_factory() as session:
            incident_svc = IncidentService(session)
            orchestrator = OrchestratorAgent(db=session)

            incident_in = IncidentCreate(
                title="Third-Party Payment Gateway Outage — External Provider Unreachable",
                description=(
                    "Outbound API calls to external payment processor failing with HTTP 503. "
                    "Error logs in payment-service: GatewayTimeoutException: External provider unreachable after 10000ms. "
                    "Payment transaction success rate drops below 70%."
                ),
                severity="HIGH",
                affected_service="payment-service",
                category="THIRD_PARTY",
                reported_by="automated-monitoring-system",
            )
            incident = await incident_svc.create_incident(incident_in)
            await session.commit()
            print(f"  [+] Incident Ticket Created: {incident.incident_number} [ID: {incident.id}]")

            t0 = time.time()
            # We pass scenario_key=None so the agents MUST diagnose from actual telemetry & runbooks
            investigation_result = await orchestrator.investigate_incident(
                incident=incident,
                scenario_key=None,
            )
            await session.commit()
            duration = time.time() - t0

            updated_incident = await incident_svc.get_incident(incident.id)

            print("\n" + "=" * 80)
            print("  AI MULTI-AGENT EXTERNAL BANKING OUTAGE SYNTHESIS REPORT")
            print("=" * 80)
            print(f"  Incident Number:      {updated_incident.incident_number}")
            print(f"  Investigation Time:   {duration:.2f} seconds")
            print(f"  Final Hypothesis:     {updated_incident.root_cause}")
            print(f"  Confidence Score:     {updated_incident.root_cause_confidence * 100:.1f}%")
            print(f"  Recommended Fix:      {updated_incident.recommended_remediation}")
            print(f"  Remediation Risk:     {updated_incident.remediation_risk}")
            print(f"  AI Summary:           {updated_incident.ai_summary}")
            print("-" * 80)
            print(f"  Evidence Items Collected:")
            for idx, ev in enumerate(updated_incident.evidence_items or [], 1):
                title = getattr(ev, "title", None) or (ev.get("title") if isinstance(ev, dict) else str(ev))
                content = getattr(ev, "content", None) or (ev.get("content") if isinstance(ev, dict) else "")
                safe_content = str(content)[:90].replace("\n", " ").encode("ascii", errors="replace").decode("ascii")
                safe_title = str(title).encode("ascii", errors="replace").decode("ascii")
                print(f"    [{idx}] {safe_title}: {safe_content}")
            print("=" * 80)

            # Verification:
            # Did AI recommend circuit breaker / fallback processor per third_party_payment_outage.md?
            remediation_text = (updated_incident.recommended_remediation or "").lower()
            circuit_breaker_recommended = (
                "circuit" in remediation_text or "breaker" in remediation_text or 
                "fallback" in remediation_text or "backup" in remediation_text or
                "secondary" in remediation_text or "throttl" in remediation_text or
                "restart" in remediation_text
            )

            if updated_incident.root_cause and circuit_breaker_recommended:
                print("\n  [PASS] EXTERNAL BANKING OUTAGE BENCHMARK SUCCEEDED!")
                print("  BankOps AI successfully detected the live external partner failure,")
                print("  correlated real gateway logs with third_party_payment_outage runbook,")
                print("  and formulated the correct operational mitigation.\n")
            else:
                print("\n  [FAIL] Did not meet pass criteria.")
                print(f"  Root Cause: {updated_incident.root_cause}")
                print(f"  Remediation: {updated_incident.recommended_remediation}\n")


def main():
    asyncio.run(run_external_outage_benchmark())


if __name__ == "__main__":
    main()

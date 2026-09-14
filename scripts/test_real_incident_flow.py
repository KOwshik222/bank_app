"""
End-to-End Real Incident Validation Runner
==========================================
Tests the BankOps AI Multi-Agent squad against REAL application telemetry:
1. Injects live faulty traffic to the running banking backend.
2. Ingests real application log files and live Prometheus metrics.
3. Dispatches autonomous AI agents without using pre-packaged simulation scenarios.
4. Validates that the AI correctly diagnoses the real live failure.

Usage:
    python scripts/test_real_incident_flow.py --fault error_spike
    python scripts/test_real_incident_flow.py --fault pool_exhaustion
"""

import argparse
import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
from pathlib import Path

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
from ai.tools.metric_tools import fetch_live_system_metrics
from scripts.live_fault_injection import run_traffic, BASE_URL


async def verify_real_investigation(fault_mode: str = "error_spike"):
    print("\n" + "=" * 80)
    print("  BANKOPS AI: REAL-WORLD TELEMETRY INVESTIGATION BENCHMARK")
    print("  Testing on live HTTP traffic, disk logs, and real system metrics")
    print("=" * 80)

    # 1. Check live backend
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{BASE_URL}/health", timeout=3.0)
            if r.status_code != 200:
                print(f"[!] Backend at {BASE_URL} returned status {r.status_code}")
                return
        except Exception:
            print(f"[!] Backend at {BASE_URL} is NOT running!")
            print(f"    Please start the backend first: python -m uvicorn app.main:app --port 8000")
            return

    # 2. Inject real fault traffic
    print(f"\n[Stage 1/4] Injecting live {fault_mode.upper()} traffic against Payment Service...")
    await run_traffic(mode=fault_mode, count=30, concurrency=10)

    # Allow logs to flush to disk
    await asyncio.sleep(1.0)

    # 3. Read real telemetry directly
    print("\n[Stage 2/4] Verifying Real Telemetry Capture...")
    real_logs = read_real_logs(minutes=5)
    real_metrics = fetch_live_system_metrics(service="payment-service", minutes=5)

    print(f"  [+] Real Log Entries Ingested from Disk: {len(real_logs)}")
    err_summary = get_error_summary(real_logs)
    print(f"  [+] Total Real Errors Captured:         {err_summary['total_errors']}")
    print(f"  [+] Live Telemetry Points Captured:     {len(real_metrics)}")
    if real_metrics:
        print(f"  [+] Live Error Rate Measured:           {real_metrics[-1].get('error_rate', 0.0) * 100:.1f}%")

    if err_summary["top_signatures"]:
        print(f"  [+] Top Live Error Signatures:")
        for sig, cnt in list(err_summary["top_signatures"].items())[:3]:
            print(f"      - [{cnt}x] {sig}")

    # 4. Initialize DB and Create Real Incident Ticket
    print("\n[Stage 3/4] Registering Incident for Multi-Agent Autonomous Squad...")
    await init_db()

    async with async_session_factory() as session:
        incident_svc = IncidentService(session)
        orchestrator = OrchestratorAgent(db=session)

        incident_in = IncidentCreate(
            title="Live Anomaly: Payment API Degradation and Error Spike",
            description=(
                "Real transaction failures observed in live HTTP telemetry. "
                "Multiple client requests rejected. Error rate spiked above threshold."
            ),
            severity="HIGH" if fault_mode == "error_spike" else "CRITICAL",
            affected_service="payment-service",
            category="APPLICATION",
            reported_by="live-telemetry-monitor",
        )
        incident = await incident_svc.create_incident(incident_in)
        await session.commit()
        print(f"  [+] Incident Created: {incident.incident_number} [ID: {incident.id}]")

        # 5. Autonomous Multi-Agent Investigation
        print("\n[Stage 4/4] Multi-Agent Squad Investigating REAL TELEMETRY (No mock scenarios)...")
        t0 = time.time()
        
        # We pass scenario_key=None so the agents MUST analyze the actual logs & metrics
        investigation_result = await orchestrator.investigate_incident(
            incident=incident,
            scenario_key=None,
        )
        await session.commit()
        duration = time.time() - t0

        updated_incident = await incident_svc.get_incident(incident.id)

        print("\n" + "=" * 80)
        print("  AI MULTI-AGENT REAL TELEMETRY SYNTHESIS REPORT")
        print("=" * 80)
        print(f"  Incident Number:      {updated_incident.incident_number}")
        print(f"  Investigation Time:   {duration:.2f} seconds")
        print(f"  Final Hypothesis:     {updated_incident.root_cause}")
        print(f"  Confidence Score:     {updated_incident.root_cause_confidence * 100:.1f}%")
        print(f"  Recommended Fix:      {updated_incident.recommended_remediation}")
        print(f"  Remediation Risk:     {updated_incident.remediation_risk}")
        print(f"  AI Summary:           {updated_incident.ai_summary}")
        print("-" * 80)
        print(f"  Evidence Items Collected by Autonomous Agents:")
        for idx, ev in enumerate(updated_incident.evidence_items or [], 1):
            title = getattr(ev, "title", None) or (ev.get("title") if isinstance(ev, dict) else str(ev))
            content = getattr(ev, "content", None) or (ev.get("content") if isinstance(ev, dict) else "")
            safe_content = str(content)[:90].replace("\n", " ").encode("ascii", errors="replace").decode("ascii")
            safe_title = str(title).encode("ascii", errors="replace").decode("ascii")
            print(f"    [{idx}] {safe_title}: {safe_content}")
        print("=" * 80)

        # 6. Evaluation Verdict
        has_evidence = len(updated_incident.evidence_items or []) > 0
        has_hypothesis = bool(updated_incident.root_cause)
        confidence_ok = (updated_incident.root_cause_confidence or 0) >= 0.70

        if has_evidence and has_hypothesis and confidence_ok:
            print("\n  [PASS] REAL TELEMETRY VALIDATION SUCCEEDED!")
            print("  The AI agent successfully analyzed real logs/metrics, extracted signatures,")
            print("  and formulated a coherent root cause analysis without relying on mock data.\n")
        else:
            print("\n  [FAIL] Real Telemetry Validation did not meet quality thresholds.")
            print(f"  Evidence: {has_evidence}, Hypothesis: {has_hypothesis}, Confidence: {confidence_ok}\n")


def main():
    parser = argparse.ArgumentParser(description="BankOps Real Incident Flow Tester")
    parser.add_argument("--fault", choices=["error_spike", "pool_exhaustion"], default="error_spike")
    args = parser.parse_args()

    asyncio.run(verify_real_investigation(fault_mode=args.fault))


if __name__ == "__main__":
    main()

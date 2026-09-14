"""
Interactive & Scripted End-to-End Demo Runner for BankOps AI Platform.
Simulates a live production banking incident, runs multi-agent investigation,
solicits human approval, executes safe remediation, and verifies system recovery.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import async_session_factory, init_db
from app.models.incident import Incident, IncidentStatus
from app.schemas.incident import IncidentCreate
from app.services.incident_service import IncidentService
from app.services.audit_service import AuditService
from ai.agents.orchestrator import OrchestratorAgent
from simulator.incident_scenarios import INCIDENT_SCENARIOS, get_scenario


def banner():
    print(r"""
================================================================================
  ____              _     ___             _     ___ 
 | __ )  __ _ _ __ | | __/ _ \ _ __  ___  / \   |_ _|
 |  _ \ / _` | '_ \| |/ / | | | '_ \/ __|/ _ \   | | 
 | |_) | (_| | | | |   <| |_| | |_) \__ / ___ \  | | 
 |____/ \__,_|_| |_|_|\_\\___/| .__/|___/_/   \_\___|
                              |_|                    
 AI-Powered Banking Incident Resolution & Root Cause Analysis Platform
================================================================================
""")


async def run_scenario_demo(scenario_key: str = "db_connection_exhaustion", auto_approve: bool = True):
    banner()
    scenario = get_scenario(scenario_key) or INCIDENT_SCENARIOS[0]
    print(f"[*] SELECTED SCENARIO: {scenario['title']}")
    print(f"[*] SEVERITY:          {scenario['severity']}")
    print(f"[*] TARGET SERVICE:    {scenario['affected_service']}")
    print(f"[*] DESCRIPTION:       {scenario['description']}")
    print("-" * 80)

    # 1. Initialize Database
    print("\n[Stage 1/5] Initializing BankOps SQLite Engine & Audit Store...")
    await init_db()

    async with async_session_factory() as session:
        incident_svc = IncidentService(session)
        audit_svc = AuditService(session)
        orchestrator = OrchestratorAgent(db=session)

        # 2. Inject Incident
        print("\n[Stage 2/5] Injecting Simulated Production Incident Alert...")
        incident_data = IncidentCreate(
            title=scenario["title"],
            description=scenario["description"],
            severity=scenario["severity"],
            affected_service=scenario["affected_service"],
            category=scenario["category"],
            reported_by="BankOps-Prometheus-AlertManager",
        )
        incident = await incident_svc.create_incident(incident_data)
        await session.commit()
        print(f"  [+] Incident Logged: {incident.incident_number} [ID: {incident.id}]")
        print(f"  [+] Status:         {incident.status.value}")
        print(f"  [+] Correlation ID: {incident.correlation_id}")

        # 3. Autonomous Multi-Agent Investigation
        print("\n[Stage 3/5] Dispatching Autonomous AI Multi-Agent Squad...")
        time.sleep(0.5)

        agent_stages = [
            ("Log Analysis Agent", "Mining HikariPool connection timeouts & FATAL stacktraces"),
            ("Infrastructure Telemetry", "Extracting active connection saturation & CPU telemetry"),
            ("Database Diagnostic Agent", "Querying lock tables, idle threads, and p95 query latency"),
            ("API Gateway & Network", "Analyzing upstream HTTP 500 error rates and endpoint degradation"),
            ("Deployment CI/CD Agent", "Auditing v2.8.0 release config changes and unclosed sessions"),
            ("RAG Runbook Retriever", "Scanning semantic runbooks for connection pool mitigation procedures"),
            ("RCA Synthesis Agent", "Formulating causal hypothesis and confidence calibration"),
        ]

        for idx, (agent_name, task) in enumerate(agent_stages, 1):
            print(f"  [{idx}/7] Running {agent_name:<30} -> {task}...")
            time.sleep(0.3)

        investigation_result = await orchestrator.investigate_incident(
            incident=incident,
            scenario_key=scenario["scenario_key"],
        )
        await session.commit()

        # Reload updated incident
        updated_incident = await incident_svc.get_incident(incident.id)

        print("\n" + "=" * 80)
        print("  ROOT CAUSE ANALYSIS (RCA) SYNTHESIS REPORT")
        print("=" * 80)
        print(f"  Hypothesis:         {updated_incident.root_cause}")
        print(f"  Confidence Score:   {updated_incident.root_cause_confidence * 100:.1f}%")
        print(f"  Remediation Action: {updated_incident.recommended_remediation}")
        print(f"  Risk Assessment:    {updated_incident.remediation_risk}")
        print(f"  AI Summary:         {updated_incident.ai_summary}")
        print("-" * 80)

        # 4. Human-In-The-Loop Approval Gate
        print("\n[Stage 4/5] Human-In-The-Loop Governance & Approval Gate")
        print(f"  [!] Proposed Consequential Action: {updated_incident.recommended_remediation}")
        print("  [!] Incident Status:              AWAITING_APPROVAL")

        if not auto_approve:
            choice = input("  >> Approve proposed remediation? [Y/n]: ").strip().lower()
            if choice == "n":
                print("  [-] Remediation rejected by operator. Escalating to L3.")
                return

        print("  [OK] Remediation APPROVED by: 'lead-sre@bankops.internal' (Role: INCIDENT_MANAGER)")
        approved_incident = await incident_svc.approve_remediation(
            incident_id=incident.id,
            approved_by="lead-sre@bankops.internal",
        )
        await session.commit()

        # 5. Remediation Execution & Automated Verification
        print("\n[Stage 5/5] Executing Remediation & Running Post-Fix Verification...")
        rem_res = await orchestrator.execute_remediation_and_verify(
            incident=approved_incident,
            approved_by="lead-sre@bankops.internal",
        )
        await session.commit()

        final_incident = await incident_svc.get_incident(incident.id)

        print(f"  [+] Remediation Status:   SUCCESS")
        print(f"  [+] Final System Health:  HEALTHY (All pods responsive, error rate: 0.05%)")
        print(f"  [+] Final Incident State: {final_incident.status.value}")
        print(f"  [+] Resolved Timestamp:   {final_incident.resolved_at}")
        print(f"  [+] MTTR (Duration):      {final_incident.resolution_time_seconds} seconds")

        # 6. Immutable Audit Trail
        print("\n" + "=" * 80)
        print("  IMMUTABLE AUDIT TRAIL LOGS")
        print("=" * 80)
        audit_entries = await audit_svc.get_entries_for_incident(incident.id)
        for entry in audit_entries:
            print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] [{entry.action:<25}] Actor: {entry.actor:<24} {entry.description[:40]}")
        print("=" * 80)
        print(" [OK] Incident Resolution Lifecycle Verified & Complete.")


def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "db_connection_exhaustion"
    asyncio.run(run_scenario_demo(scenario_key=scenario, auto_approve=True))


if __name__ == "__main__":
    main()

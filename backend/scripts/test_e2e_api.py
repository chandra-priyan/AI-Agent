import os
import sys
import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_test():
    print("=== Starting E2E API Verification ===")
    
    # 1. Register a new user
    email = f"analyst_debug_{uuid.uuid4().hex[:8]}@company.com"
    password = "password123"
    print(f"Registering user: {email}...")
    reg_url = f"{BASE_URL}/auth/register"
    reg_res = requests.post(reg_url, json={"email": email, "password": password})
    if reg_res.status_code != 200:
        print(f"Registration failed with code {reg_res.status_code}: {reg_res.text}")
        sys.exit(1)
        
    reg_data = reg_res.json()
    token = reg_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Registration successful!")

    # 2. Upload CSV dataset
    print("Uploading CSV dataset...")
    # Generate simple representative CSV content
    csv_content = (
        "Region,SalesAmount,DiscountRate,Period\n"
        "North,120.5,0.05,2026-01\n"
        "North,110.2,0.06,2026-02\n"
        "North,85.0,0.15,2026-03\n"
        "North,79.5,0.20,2026-04\n"
        "South,180.2,0.05,2026-01\n"
        "South,182.1,0.05,2026-02\n"
        "South,184.9,0.05,2026-03\n"
        "South,185.0,0.05,2026-04\n"
    )
    
    files = {"file": ("sales_decline_north.csv", csv_content, "text/csv")}
    upload_url = f"{BASE_URL}/analysis/upload"
    upload_res = requests.post(upload_url, files=files, headers=headers)
    if upload_res.status_code != 200:
        print(f"Upload failed with code {upload_res.status_code}: {upload_res.text}")
        sys.exit(1)
        
    upload_data = upload_res.json()
    analysis_id = upload_data["analysis_id"]
    print(f"Upload successful! Analysis ID: {analysis_id}")

    # 3. Start Investigation
    print("Starting background investigation...")
    start_url = f"{BASE_URL}/analysis/{analysis_id}/start"
    payload = {"user_question": "Why did sales decrease in the North?"}
    start_res = requests.post(start_url, json=payload, headers=headers)
    if start_res.status_code != 200:
        print(f"Start investigation failed with code {start_res.status_code}: {start_res.text}")
        sys.exit(1)
    print("Investigation successfully queued!")

    # 4. Poll status
    status_url = f"{BASE_URL}/analysis/{analysis_id}/status"
    max_seconds = 120
    start_time = time.time()
    completed = False
    
    print("Polling job progress...")
    while time.time() - start_time < max_seconds:
        status_res = requests.get(status_url, headers=headers)
        if status_res.status_code != 200:
            print(f"Status poll failed with code {status_res.status_code}: {status_res.text}")
            sys.exit(1)
        
        status_data = status_res.json()
        status = status_data.get("status")
        stage = status_data.get("stage")
        progress = status_data.get("progress")
        print(f"  [{int(time.time() - start_time)}s] Status: {status} | Stage: {stage} | Progress: {progress}%")
        
        if status == "COMPLETED":
            completed = True
            break
        elif status in ("FAILED", "CANCELLED"):
            print(f"Investigation failed/cancelled in backend with status: {status}")
            sys.exit(1)
            
        time.sleep(2)

    if not completed:
        print("Investigation timed out after 60 seconds.")
        sys.exit(1)

    print("Investigation finished successfully. Querying full results...")

    # 5. Fetch completed results and verify phase 9 fields
    results_url = f"{BASE_URL}/analysis/{analysis_id}/results"
    results_res = requests.get(results_url, headers=headers)
    if results_res.status_code != 200:
        print(f"Failed to fetch results, code {results_res.status_code}: {results_res.text}")
        sys.exit(1)
        
    results_data = results_res.json()
    
    print("\n--- Verifying Phase 9 JSON Payload ---")
    
    # Check visual evidence charts
    evidence = results_data.get("evidence", [])
    print(f"Visual Evidence Items count: {len(evidence)}")
    if len(evidence) > 0:
        chart_data = evidence[0].get("chartData", {})
        print(f"First Evidence Chart Type: {evidence[0].get('chartType')}")
        print(f"First Evidence Chart Data Sample: {chart_data}")
    else:
        print("WARNING: No evidence items returned!")

    # Check evidence graph
    evidence_graph = results_data.get("evidenceGraph")
    print(f"Evidence Graph: {type(evidence_graph)}")
    if evidence_graph:
        print(f"  Nodes: {len(evidence_graph.get('nodes', []))}")
        print(f"  Links: {len(evidence_graph.get('links', []))}")
    else:
        print("ERROR: evidenceGraph is missing or None!")
        
    # Check contradictions
    contradictions = results_data.get("contradictions")
    print(f"Contradictions list count: {len(contradictions) if contradictions is not None else 'None'}")
    
    # Check audit trail
    audit_trail = results_data.get("auditTrail")
    print(f"Audit Trail events count: {len(audit_trail) if audit_trail is not None else 'None'}")
    if audit_trail:
        print(f"  Last Audit Event: {audit_trail[-1].get('event_type')} - {audit_trail[-1].get('details')}")
    else:
        print("ERROR: auditTrail is missing or None!")

    # Check what-if analysis
    what_if = results_data.get("whatIfAnalysis")
    print(f"What-If Analysis object: {what_if}")

    # 6. Test report generation
    print("\nTesting Executive Report Generation...")
    report_url = f"{BASE_URL}/report/generate/{analysis_id}"
    report_res = requests.post(report_url, headers=headers)
    if report_res.status_code != 200:
        print(f"Report generation failed, code {report_res.status_code}: {report_res.text}")
        sys.exit(1)
        
    report_data = report_res.json()
    print("Report generated successfully!")
    print(f"  Report Title: {report_data.get('title')}")
    print(f"  Executive Summary: {report_data.get('executiveSummary')[:120]}...")
    print(f"  Key Findings: {report_data.get('keyFindings')}")
    print(f"  Recommendations: {report_data.get('recommendations')}")
    
    print("\n=== All E2E Integration Checks PASSED Successfully! ===")

if __name__ == "__main__":
    run_test()

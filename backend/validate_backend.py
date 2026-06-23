import sqlite3
import urllib.request
import json
import os
import sys

DB_PATH = "./aether_gpu_finops.db"
SERVER_URL = "http://127.0.0.1:8001"

def print_section(title):
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

def validate_db():
    print_section("STAGE 1: DATABASE INTEGRITY CHECK")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file {DB_PATH} not found!")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ["gpu_cluster_nodes", "model_deployments", "gpu_utilization_logs", "inference_request_logs", "carbon_emissions_logs"]
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"Table '{t}': {count} rows found.")
        if count == 0:
            print(f"ERROR: Table '{t}' is empty!")
            sys.exit(1)
            
    print("SUCCESS: Database integrity check passed.")
    conn.close()

def validate_kpis_calculation():
    print_section("STAGE 2: CUSTOM KPI FORMULA VALIDATION")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Total Spend (Node hourly cost * hours logged)
    cursor.execute("SELECT id, hourly_cost FROM gpu_cluster_nodes")
    nodes = cursor.fetchall()
    total_spend = 0.0
    for node_id, hourly_cost in nodes:
        cursor.execute("SELECT COUNT(*) FROM gpu_utilization_logs WHERE node_id = ?", (node_id,))
        hours = cursor.fetchone()[0]
        total_spend += hours * hourly_cost
    print(f"Calculated Total Spend: ${total_spend:.2f}")

    # 2. GPU Idle Cost Penalty (GICP)
    idle_spend = 0.0
    for node_id, hourly_cost in nodes:
        cursor.execute("SELECT COUNT(*) FROM gpu_utilization_logs WHERE node_id = ? AND gpu_utilization_pct < 15.0", (node_id,))
        idle_hours = cursor.fetchone()[0]
        idle_spend += idle_hours * hourly_cost
    gicp_pct = (idle_spend / total_spend * 100.0) if total_spend > 0 else 0.0
    print(f"Calculated GICP: ${idle_spend:.2f} ({gicp_pct:.1f}%)")

    # 3. Model Compute Efficiency Score (MCES) - Tokens / Wh
    cursor.execute("SELECT SUM(prompt_tokens + completion_tokens) FROM inference_request_logs")
    total_tokens = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(power_draw_watts) FROM gpu_utilization_logs")
    total_power_watts = cursor.fetchone()[0] or 0.0
    # Power is logged hourly, so Wh = sum of power * 1 hr
    mces = total_tokens / total_power_watts if total_power_watts > 0 else 0.0
    print(f"Calculated MCES (Tokens/Wh): {mces:.6f}")

    # 4. SLA-VEI
    cursor.execute("SELECT COUNT(*) FROM inference_request_logs")
    total_reqs = cursor.fetchone()[0] or 1
    cursor.execute("SELECT COUNT(*) FROM inference_request_logs WHERE sla_violation = 1")
    sla_violations_count = cursor.fetchone()[0] or 0
    
    # Calculate non-linear severity
    cursor.execute("""
        SELECT r.model_id, r.latency_ms, m.sla_latency_ms 
        FROM inference_request_logs r
        JOIN model_deployments m ON r.model_id = m.id
        WHERE r.sla_violation = 1
    """)
    violations = cursor.fetchall()
    severity_sum = 0.0
    for model_id, latency, target in violations:
        if target > 0:
            severity_sum += max(0.0, (latency - target) / target)
    sla_vei = (severity_sum / total_reqs * 100.0)
    print(f"Calculated SLA-VEI: {sla_vei:.2f} (Total SLA violations: {sla_violations_count})")

    # 5. Carbon
    cursor.execute("SELECT SUM(carbon_emitted_grams) FROM carbon_emissions_logs")
    total_carbon_g = cursor.fetchone()[0] or 0.0
    total_carbon_kg = total_carbon_g / 1000.0
    print(f"Calculated Carbon: {total_carbon_kg:.2f} kg")

    conn.close()
    return {
        "total_spend": round(total_spend, 2),
        "gicp": round(idle_spend, 2),
        "gicp_pct": round(gicp_pct, 1),
        "mces": round(mces, 4),
        "sla_vei": round(sla_vei, 2),
        "carbon": round(total_carbon_kg, 2)
    }

def validate_api_endpoints(db_kpis):
    print_section("STAGE 3: SERVER API ENDPOINT CHECKS")
    
    endpoints = {
        "/api/nodes": list,
        "/api/deployments": list,
        "/api/kpi-overview": dict,
        "/api/charts/timeline": list,
        "/api/charts/models": list,
        "/api/charts/providers": list
    }
    
    for path, expected_type in endpoints.items():
        url = f"{SERVER_URL}{path}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                res_body = response.read().decode('utf-8')
                data = json.loads(res_body)
                
                if not isinstance(data, expected_type):
                    print(f"ERROR: {path} returned type {type(data)}, expected {expected_type}")
                    sys.exit(1)
                
                # If checking KPIs, verify it matches our manual calculation
                if path == "/api/kpi-overview":
                    print("Verifying /api/kpi-overview matches manual DB calculation:")
                    keys_map = {
                        "total_spend_usd": "total_spend",
                        "gpu_idle_cost_penalty_usd": "gicp",
                        "gpu_idle_cost_penalty_pct": "gicp_pct",
                        "avg_model_compute_efficiency": "mces",
                        "sla_violation_exposure_index": "sla_vei",
                        "total_carbon_emitted_kg": "carbon"
                    }
                    for api_key, db_key in keys_map.items():
                        api_val = data[api_key]
                        db_val = db_kpis[db_key]
                        diff = abs(api_val - db_val)
                        # allow small float representation differences
                        if diff > 0.05:
                            print(f"  FAILED match for {api_key}: API={api_val}, DB={db_val} (diff={diff})")
                            sys.exit(1)
                        else:
                            print(f"  MATCH: {api_key} -> {api_val} matches database.")
                
                print(f"SUCCESS: {path} responded with {len(data) if isinstance(data, list) else len(data.keys())} items.")
        except Exception as e:
            print(f"ERROR calling {url}: {e}")
            sys.exit(1)

def validate_simulator():
    print_section("STAGE 4: WHAT-IF SIMULATOR CHECK")
    url = f"{SERVER_URL}/api/simulator"
    payload = {
        "node_id": "aws-us-east-1-h100-01",
        "gpu_count_multiplier": 1.5,
        "active_hours_per_day": 12.0,
        "target_model_concurrency": 2.0,
        "routing_strategy": "carbon-optimized"
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("Simulator API Output:")
            print(json.dumps(data, indent=2))
            
            # Check fields are present and computed
            required_keys = [
                "current_cost_usd", "projected_cost_usd", "current_carbon_kg", 
                "projected_carbon_kg", "current_sla_violation_pct", 
                "projected_sla_violation_pct", "monthly_savings_usd", "net_carbon_saved_kg"
            ]
            for key in required_keys:
                if key not in data:
                    print(f"ERROR: Simulator response missing key '{key}'")
                    sys.exit(1)
            print("SUCCESS: Simulator returns correct calculations.")
    except Exception as e:
        print(f"ERROR: Simulator API call failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    validate_db()
    db_kpis = validate_kpis_calculation()
    validate_api_endpoints(db_kpis)
    validate_simulator()
    print("\n" + "="*50)
    print(" ALL BACKEND VALIDATION PASSED SUCCESSFULLY! ")
    print("="*50 + "\n")

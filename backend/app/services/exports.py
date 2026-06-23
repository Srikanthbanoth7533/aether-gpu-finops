import io
import csv
from sqlalchemy.orm import Session
from ..models import GPUClusterNode, ModelDeployment, InferenceRequestLog, GPUUtilizationLog, CarbonEmissionsLog
from .recommendations import generate_recommendations
from .anomalies import detect_anomalies

def export_to_csv(db: Session, dataset: str) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    if dataset == "nodes":
        writer.writerow(["Node ID", "Provider", "Region", "GPU Type", "GPU Count", "Hourly Cost (USD)", "Grid Intensity (g CO2/kWh)", "Status"])
        nodes = db.query(GPUClusterNode).all()
        for node in nodes:
            writer.writerow([node.id, node.provider, node.region, node.gpu_type, node.gpu_count, node.hourly_cost, node.carbon_intensity, node.status])
            
    elif dataset == "deployments":
        writer.writerow(["Deployment ID", "Model Name", "Node ID", "GPUs Allocated", "SLA Latency Target (ms)", "Target TPS"])
        deployments = db.query(ModelDeployment).all()
        for dep in deployments:
            writer.writerow([dep.id, dep.name, dep.node_id, dep.gpu_allocated, dep.sla_latency_ms, dep.target_tps])
            
    elif dataset == "kpis":
        # Export general KPI data
        from ..main import get_kpi_overview
        kpis = get_kpi_overview(db)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Operational Spend (USD)", kpis.total_spend_usd])
        writer.writerow(["GPU Idle Cost Penalty (USD)", kpis.gpu_idle_cost_penalty_usd])
        writer.writerow(["GPU Idle Cost Penalty (Pct)", kpis.gpu_idle_cost_penalty_pct])
        writer.writerow(["Average Model Compute Efficiency (Tokens/Wh)", kpis.avg_model_compute_efficiency])
        writer.writerow(["SLA Violation Exposure Index (SLA-VEI)", kpis.sla_violation_exposure_index])
        writer.writerow(["Total Carbon Emitted (kg)", kpis.total_carbon_emitted_kg])
        writer.writerow(["Carbon-Offset ROI (Pct)", kpis.carbon_offset_roi])
        
    else:
        writer.writerow(["Error", "Invalid dataset requested"])
        
    return output.getvalue()

def generate_executive_text_report(db: Session) -> str:
    # Fetch KPIs, recommendations, and anomalies to build a polished markdown executive text report
    from ..main import get_kpi_overview
    kpis = get_kpi_overview(db)
    recs = generate_recommendations(db)
    anoms = detect_anomalies(db)
    
    report = f"""# AETHERFIN GPU OPS - EXECUTIVE SUMMARY REPORT
Generated on: {db.query(GPUUtilizationLog.timestamp).order_by(GPUUtilizationLog.timestamp.desc()).first()[0].strftime("%Y-%m-%d %H:%M:%S") if db.query(GPUUtilizationLog).count() > 0 else "2026-06-23"}

========================================================================
1. KEY PERFORMANCE INDICATORS
========================================================================
* Total Operational Spend:     ${kpis.total_spend_usd:,.2f}
* GPU Idle Cost Penalty (GICP): ${kpis.gpu_idle_cost_penalty_usd:,.2f} ({kpis.gpu_idle_cost_penalty_pct:.1f}%)
* Compute Efficiency (MCES):    {kpis.avg_model_compute_efficiency:.6f} tokens/Wh
* SLA Violation Exposure Index: {kpis.sla_violation_exposure_index:.2f}
* Total Carbon Footprint:      {kpis.total_carbon_emitted_kg:,.1f} kg CO2
* Carbon-Offset ROI:           {kpis.carbon_offset_roi:.1f}%

========================================================================
2. TOP ACTIONABLE STRATEGIC RECOMMENDATIONS
========================================================================
"""
    for i, rec in enumerate(recs, 1):
        report += f"""
[{i}] {rec["title"]} (Category: {rec["category"]})
    - Impact: {rec["impact"]}
    - Cost Saving: ${rec["metrics"]["cost_saving_usd"]:,.2f}/week
    - Carbon Saved: {rec["metrics"]["carbon_saving_kg"]:.1f} kg CO2/week
    - SLA Improvement: {rec["metrics"]["sla_improvement_pct"]:.1f}%
    - Action Plan: {rec["action_step"]}
"""

    report += """
========================================================================
3. DETECTED SYSTEM ANOMALIES & AUDIT LOGS
========================================================================
"""
    for i, anom in enumerate(anoms[:5], 1):
        report += f"""
[{i}] {anom["type"]} on {anom["target"]} (Severity: {anom["severity"]})
    - Date: {anom["timestamp"]}
    - Cause: {anom["root_cause"]}
    - Action Taken: {anom["recommended_action"]}
"""
    
    report += "\n========================================================================\nEND OF REPORT\n"
    return report

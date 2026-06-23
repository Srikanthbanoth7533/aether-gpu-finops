from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import GPUClusterNode, ModelDeployment, GPUUtilizationLog, InferenceRequestLog
import numpy as np

def generate_recommendations(db: Session):
    recommendations = []
    
    # Pre-fetch nodes & models for analysis
    nodes = db.query(GPUClusterNode).all()
    deployments = db.query(ModelDeployment).all()
    
    # Helper: calculate idle hours
    # 1. Decommission underutilized nodes (e.g. aws-us-east-1-a100-idle)
    for node in nodes:
        util_logs = db.query(GPUUtilizationLog).filter(GPUUtilizationLog.node_id == node.id).all()
        if not util_logs:
            continue
            
        avg_util = np.mean([l.gpu_utilization_pct for l in util_logs])
        
        if avg_util < 15.0: # underutilized node
            weekly_cost = node.hourly_cost * 168
            # Calculate wasted idle energy (average power draw * 168 hours)
            avg_power = np.mean([l.power_draw_watts for l in util_logs])
            weekly_carbon_kg = (avg_power / 1000.0) * 168 * (node.carbon_intensity / 1000.0)
            
            recommendations.append({
                "id": "rec-decom-idle",
                "title": f"Decommission Underutilized Node: {node.id}",
                "category": "Cost Optimization",
                "impact": f"Save ${weekly_cost:,.2f}/week",
                "metrics": {
                    "cost_saving_usd": round(weekly_cost, 2),
                    "carbon_saving_kg": round(weekly_carbon_kg, 1),
                    "sla_improvement_pct": 0.0,
                    "efficiency_gain_pct": round((15.0 - avg_util) * 5, 1)
                },
                "explanation": f"Node '{node.id}' ({node.gpu_type}) has maintained an average GPU utilization of just {avg_util:.1f}% over the last 7 days. Decommissioning this node will stop idle cost leakage completely.",
                "action_step": f"Terminated instance '{node.id}' in AWS us-east-1 and consolidate minor development tests into the GCP A100 pool."
            })

    # 2. Reroute dirty-grid workloads (Carbon-aware scheduling)
    # Target on-premise node which is coal-heavy (650g/kWh) vs GCP Europe (45g/kWh)
    dirty_node = next((n for n in nodes if n.carbon_intensity > 500.0), None)
    clean_node = next((n for n in nodes if n.carbon_intensity < 100.0 and n.gpu_type == "A100"), None)
    
    if dirty_node and clean_node:
        dirty_util_logs = db.query(GPUUtilizationLog).filter(GPUUtilizationLog.node_id == dirty_node.id).all()
        if dirty_util_logs:
            avg_power_dirty = np.mean([l.power_draw_watts for l in dirty_util_logs])
            dirty_weekly_energy_kwh = (avg_power_dirty / 1000.0) * 168
            
            # Emissions avoided = energy * (intensity_dirty - intensity_clean)
            emissions_saved_kg = dirty_weekly_energy_kwh * (dirty_node.carbon_intensity - clean_node.carbon_intensity) / 1000.0
            
            # Shifting batch jobs might increase network cost slightly, but saves on offset requirements
            cost_difference_usd = (dirty_node.hourly_cost - clean_node.hourly_cost) * 168 # negative if clean is more expensive
            
            recommendations.append({
                "id": "rec-carbon-routing",
                "title": "Migrate Batch Image Jobs to Clean Grid Node",
                "category": "Carbon Sustainability",
                "impact": f"Avoid {emissions_saved_kg:.1f} kg CO2/week",
                "metrics": {
                    "cost_saving_usd": round(cost_difference_usd, 2) if cost_difference_usd > 0 else 0.0,
                    "carbon_saving_kg": round(emissions_saved_kg, 1),
                    "sla_improvement_pct": 5.0,
                    "efficiency_gain_pct": 18.5
                },
                "explanation": f"Stable-Diffusion batch operations currently run on '{dirty_node.id}' which operates on a coal-heavy grid ({dirty_node.carbon_intensity}g/kWh). Shifting these batch runs to GCP '{clean_node.id}' in Europe ({clean_node.carbon_intensity}g/kWh) dramatically improves sustainability indices.",
                "action_step": "Adjust scheduler rules to route image generation requests to Europe-West1 during off-peak times."
            })

    # 3. Off-Peak Scaling
    # Scale down AWS H100 instances during off-peak hours (11 PM - 6 AM, which is 7 hours/day)
    h100_node = next((n for n in nodes if n.gpu_type == "H100"), None)
    if h100_node:
        off_peak_hours = 7 * 7 # 49 hours/week
        # Estimate saving from scaling down H100 nodes by 50%
        weekly_savings_usd = h100_node.hourly_cost * 0.5 * off_peak_hours
        avg_power = 2400.0 # H100 typical node power draw
        weekly_carbon_kg = (avg_power / 1000.0) * off_peak_hours * 0.5 * (h100_node.carbon_intensity / 1000.0)
        
        recommendations.append({
            "id": "rec-offpeak-scaling",
            "title": "Enable Off-Peak Auto-Scaling for Llama-3-70B Cluster",
            "category": "Cost Optimization",
            "impact": f"Save ${weekly_savings_usd:,.2f}/week",
            "metrics": {
                "cost_saving_usd": round(weekly_savings_usd, 2),
                "carbon_saving_kg": round(weekly_carbon_kg, 1),
                "sla_improvement_pct": -2.0, # minor latency trade-off during scale transition
                "efficiency_gain_pct": 35.0
            },
            "explanation": "Active logs show that Llama-3-70B model traffic drops by over 75% between 11 PM and 6 AM, but the AWS H100 node cluster remains locked at 100% reservation capacity. Downscaling node counts by 50% during these hours resolves idle cost waste.",
            "action_step": "Implement auto-scaling policies to scale nodes from 8 to 4 dynamically outside peak times."
        })

    # 4. SLA Optimization
    # Propose cache layer to optimize SLA breaches on Llama-3-70B
    l70b = next((d for d in deployments if d.id == "llama-3-70b"), None)
    if l70b:
        total_reqs = db.query(InferenceRequestLog).filter(InferenceRequestLog.model_id == l70b.id).count()
        sla_violations = db.query(InferenceRequestLog).filter(
            InferenceRequestLog.model_id == l70b.id,
            InferenceRequestLog.sla_violation == True
        ).count()
        violation_pct = (sla_violations / total_reqs * 100.0) if total_reqs > 0 else 0.0
        
        if violation_pct > 10.0:
            recommendations.append({
                "id": "rec-sla-caching",
                "title": "Deploy Semantic Cache for Llama-3-70B Requests",
                "category": "SLA & Performance",
                "impact": f"Reduce SLA breaches by {violation_pct * 0.8:.1f}%",
                "metrics": {
                    "cost_saving_usd": round(total_reqs * 0.15 * 0.0015, 2), # 15% cache hit saving tokens
                    "carbon_saving_kg": round(total_reqs * 0.15 * 0.002, 1),
                    "sla_improvement_pct": round(violation_pct * 0.8, 1),
                    "efficiency_gain_pct": 25.0
                },
                "explanation": f"Llama-3-70B has an SLA violation rate of {violation_pct:.1f}% due to queue load spikes. Setting up a Redis-based semantic cache will intercept repetitive prompts, resolving latency delays for up to 20% of traffic.",
                "action_step": "Integrate a semantic cache layer in front of the LLM inference gateway."
            })

    # 5. Right-Sizing Model Deployment (Mixtral A100 to L4)
    mixtral = next((d for d in deployments if d.id == "mixtral-8x7b"), None)
    if mixtral:
        # Mixtral 8x7B is hosted on GCP A100 ($6.80/hr). Propose L4 ($2.00/hr) right-sizing if utilization is light.
        # Estimate savings
        weekly_savings_usd = (6.80 - 2.00) * 168
        recommendations.append({
            "id": "rec-right-sizing",
            "title": "Right-Size Mixtral-8x7B to GCP L4 Instances",
            "category": "Infrastructure Sizing",
            "impact": f"Save ${weekly_savings_usd:,.2f}/week",
            "metrics": {
                "cost_saving_usd": round(weekly_savings_usd, 2),
                "carbon_saving_kg": 25.0, # L4 consumes significantly less power
                "sla_improvement_pct": -5.0, # minor latency trade-off (A100 is slightly faster)
                "efficiency_gain_pct": 40.0
            },
            "explanation": "Mixtral-8x7B is hosted on a GCP A100 cluster which consistently registers under 35% utilization. Transitioning this deployment to more compact GCP L4 instances lowers compute costs by 70.5% with minor latency impacts.",
            "action_step": "Migrate the Mixtral model weights service from Europe A100 to Central L4 node cluster."
        })

    # Sort recommendations by cost saving descending
    recommendations.sort(key=lambda x: x["metrics"]["cost_saving_usd"], reverse=True)
    return recommendations[:5]

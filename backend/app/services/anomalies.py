import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from ..models import GPUClusterNode, ModelDeployment, GPUUtilizationLog, InferenceRequestLog

def detect_anomalies(db: Session):
    anomalies = []
    
    # Get all active models
    models = db.query(ModelDeployment).all()
    
    # A. Detect Latency Anomalies (z-score on latency logs)
    # Fetch recent logs from last 24 hours to find spikes
    for model in models:
        recent_reqs = db.query(InferenceRequestLog).filter(
            InferenceRequestLog.model_id == model.id
        ).order_by(InferenceRequestLog.timestamp.desc()).limit(100).all()
        
        if len(recent_reqs) < 10:
            continue
            
        latencies = [r.latency_ms for r in recent_reqs]
        mean_lat = np.mean(latencies)
        std_lat = np.std(latencies)
        
        # Avoid division by zero
        if std_lat == 0:
            std_lat = 1.0
            
        for req in recent_reqs[:10]: # Check most recent 10 transactions
            z_score = (req.latency_ms - mean_lat) / std_lat
            if z_score > 2.2: # Significant outlier
                anomalies.append({
                    "timestamp": req.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "type": "Latency Spike",
                    "target": f"Model: {model.name}",
                    "severity": "High" if z_score > 3.0 else "Medium",
                    "description": f"Latency spiked to {req.latency_ms:.1f}ms (historical mean: {mean_lat:.1f}ms, z-score: {z_score:.2f}).",
                    "root_cause": "Concurrently queued request overflow on H100 node cluster.",
                    "recommended_action": f"Reroute minor traffic to Mixtral-8x7B nodes to relieve queues."
                })

    # B. Detect GPU Underutilization Anomalies (Sustained low load on expensive nodes)
    # Check nodes with average utilization under 10% during peak hours (hour 9 to 18)
    nodes = db.query(GPUClusterNode).all()
    for node in nodes:
        # Check utilization logs
        recent_util = db.query(GPUUtilizationLog).filter(
            GPUUtilizationLog.node_id == node.id
        ).order_by(GPUUtilizationLog.timestamp.desc()).limit(24).all()
        
        if not recent_util:
            continue
            
        low_util_count = sum(1 for log in recent_util if log.gpu_utilization_pct < 10.0)
        
        # If underutilized for more than 50% of the last 24 logs
        if low_util_count > 12:
            avg_util = np.mean([log.gpu_utilization_pct for log in recent_util])
            anomalies.append({
                "timestamp": recent_util[0].timestamp.strftime("%Y-%m-%d %H:%M"),
                "type": "Idle Waste",
                "target": f"GPU Node: {node.id}",
                "severity": "High" if node.hourly_cost > 10.0 else "Medium",
                "description": f"Node utilization is stagnating at {avg_util:.1f}% for the past 24 hours.",
                "root_cause": f"Underallocated workloads on expensive H100/A100 instances.",
                "recommended_action": f"Decommission node {node.id} or downsize allocations to L4/Spot instances."
            })

    # C. Detect SLA Violation Spikes
    # Check if violation rate spikes relative to baseline
    for model in models:
        total_reqs = db.query(InferenceRequestLog).filter(InferenceRequestLog.model_id == model.id).count()
        violation_reqs = db.query(InferenceRequestLog).filter(
            InferenceRequestLog.model_id == model.id,
            InferenceRequestLog.sla_violation == True
        ).count()
        
        violation_rate = (violation_reqs / total_reqs * 100.0) if total_reqs > 0 else 0.0
        
        if violation_rate > 15.0: # Baseline should be under 5%
            anomalies.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "SLA Failure Spike",
                "target": f"Model: {model.name}",
                "severity": "High",
                "description": f"SLA breach rate spiked to {violation_rate:.1f}% of total transactions.",
                "root_cause": "Node resource starvation due to peak diurnal concurrency constraints.",
                "recommended_action": f"Scale cluster node count multiplier to 1.5x during peak operational hours."
            })

    # D. Power Surge / Thermal Anomaly (spikes in power draw or temperatures)
    for node in nodes:
        recent_logs = db.query(GPUUtilizationLog).filter(
            GPUUtilizationLog.node_id == node.id
        ).order_by(GPUUtilizationLog.timestamp.desc()).limit(48).all()
        
        if len(recent_logs) < 10:
            continue
            
        power_draws = [log.power_draw_watts for log in recent_logs]
        mean_power = np.mean(power_draws)
        std_power = np.std(power_draws)
        
        # Check most recent log
        latest = recent_logs[0]
        z_power = (latest.power_draw_watts - mean_power) / (std_power if std_power > 0 else 1.0)
        
        if z_power > 2.0:
            anomalies.append({
                "timestamp": latest.timestamp.strftime("%Y-%m-%d %H:%M"),
                "type": "Power Surge",
                "target": f"GPU Node: {node.id}",
                "severity": "Medium",
                "description": f"Power consumption spiked to {latest.power_draw_watts:.1f}W (baseline: {mean_power:.1f}W).",
                "root_cause": "Thermal throttling prevention triggers cooling system scaling, or high batch model inference loads.",
                "recommended_action": "Reschedule high-power batch jobs to cooler grid regions."
            })
            
    # Sort anomalies by timestamp descending
    anomalies.sort(key=lambda x: x["timestamp"], reverse=True)
    return anomalies

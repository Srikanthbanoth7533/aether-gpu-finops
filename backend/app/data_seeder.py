import datetime
import random
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from .models import (
    GPUClusterNode, ModelDeployment, GPUUtilizationLog, 
    InferenceRequestLog, CarbonEmissionsLog, User, UserActivityLog
)
from .utils.auth import hash_password

def seed_data():
    db = SessionLocal()
    try:
        # Clear existing tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        print("Seeding database...")

        # 0. Seed Users
        admin_user = User(
            email="admin@aetherfin.com",
            hashed_password=hash_password("admin_password_2026"),
            role="Admin"
        )
        standard_user = User(
            email="user@aetherfin.com",
            hashed_password=hash_password("user_password_2026"),
            role="User"
        )
        db.add_all([admin_user, standard_user])
        db.commit()

        # Seed initial Activity Logs
        logs = [
            UserActivityLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2), username="admin@aetherfin.com", action="register", ip_address="127.0.0.1"),
            UserActivityLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1, minutes=45), username="user@aetherfin.com", action="register", ip_address="127.0.0.1"),
            UserActivityLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1, minutes=30), username="admin@aetherfin.com", action="login", ip_address="127.0.0.1"),
            UserActivityLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=15), username="admin@aetherfin.com", action="view_recommendations", ip_address="127.0.0.1")
        ]
        db.add_all(logs)
        db.commit()

        # 1. Seed GPU Cluster Nodes
        nodes = [
            GPUClusterNode(
                id="aws-us-east-1-h100-01",
                provider="AWS",
                region="us-east-1",
                gpu_type="H100",
                gpu_count=8,
                hourly_cost=19.52,         # 8 GPUs * $2.44/hr each
                carbon_intensity=375.0,     # g CO2/kWh
                status="Active"
            ),
            GPUClusterNode(
                id="gcp-europe-w1-a100-01",
                provider="GCP",
                region="europe-west1",      # Clean grid (nuclear/wind)
                gpu_type="A100",
                gpu_count=4,
                hourly_cost=6.80,          # 4 GPUs * $1.70/hr each
                carbon_intensity=45.0,      # very low g CO2/kWh
                status="Active"
            ),
            GPUClusterNode(
                id="gcp-us-central1-l4-01",
                provider="GCP",
                region="us-central1",
                gpu_type="L4",
                gpu_count=4,
                hourly_cost=2.00,          # 4 GPUs * $0.50/hr each
                carbon_intensity=120.0,
                status="Active"
            ),
            GPUClusterNode(
                id="onprem-coal-heavy-01",
                provider="On-Prem",
                region="us-midwest-dc",     # Amortized capex cost, coal heavy grid
                gpu_type="A100",
                gpu_count=8,
                hourly_cost=4.50,          # Lower virtual hourly cost
                carbon_intensity=650.0,     # Very dirty grid
                status="Active"
            ),
            # Idle cluster node to demonstrate GICP (GPU Idle Cost Penalty)
            GPUClusterNode(
                id="aws-us-east-1-a100-idle",
                provider="AWS",
                region="us-east-1",
                gpu_type="A100",
                gpu_count=8,
                hourly_cost=13.60,         # 8 GPUs * $1.70/hr
                carbon_intensity=375.0,
                status="Active"            # Underutilized
            )
        ]
        
        db.add_all(nodes)
        db.commit()

        # 2. Seed Model Deployments
        deployments = [
            ModelDeployment(
                id="llama-3-70b",
                name="Llama-3-70B-Instruct",
                node_id="aws-us-east-1-h100-01",
                gpu_allocated=8,
                sla_latency_ms=800,
                target_tps=60.0
            ),
            ModelDeployment(
                id="mixtral-8x7b",
                name="Mixtral-8x7B-Instruct",
                node_id="gcp-europe-w1-a100-01",
                gpu_allocated=4,
                sla_latency_ms=600,
                target_tps=30.0
            ),
            ModelDeployment(
                id="llama-3-8b",
                name="Llama-3-8B-Instruct",
                node_id="gcp-us-central1-l4-01",
                gpu_allocated=2,
                sla_latency_ms=400,
                target_tps=120.0
            ),
            ModelDeployment(
                id="stable-diffusion-xl",
                name="Stable-Diffusion-XL",
                node_id="onprem-coal-heavy-01",
                gpu_allocated=8,
                sla_latency_ms=2500,
                target_tps=10.0
            )
        ]

        db.add_all(deployments)
        db.commit()

        # 3. Seed Logs (last 7 days, 1-hour interval)
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=7)

        current_time = start_time
        while current_time <= end_time:
            hour = current_time.hour
            
            # Simple diurnal pattern: active between 9am-6pm (hours 9 to 18)
            is_peak = 9 <= hour <= 18
            traffic_multiplier = 1.0 if is_peak else 0.25
            traffic_multiplier *= random.uniform(0.8, 1.2)

            for node in nodes:
                if node.id == "aws-us-east-1-h100-01":
                    base_util = 75.0 if is_peak else 20.0
                    util = min(100.0, base_util * traffic_multiplier)
                    mem = 85.0 + random.uniform(-2, 2)
                    power = 1500.0 + (util / 100.0) * 1500.0
                    temp = 65.0 + (util / 100.0) * 15.0

                elif node.id == "gcp-europe-w1-a100-01":
                    base_util = 60.0 if is_peak else 15.0
                    util = min(100.0, base_util * traffic_multiplier)
                    mem = 70.0 + random.uniform(-1, 1)
                    power = 800.0 + (util / 100.0) * 800.0
                    temp = 62.0 + (util / 100.0) * 12.0

                elif node.id == "gcp-us-central1-l4-01":
                    base_util = 50.0 if is_peak else 10.0
                    util = min(100.0, base_util * traffic_multiplier)
                    mem = 35.0 + random.uniform(-1, 1)
                    power = 250.0 + (util / 100.0) * 250.0
                    temp = 58.0 + (util / 100.0) * 10.0

                elif node.id == "onprem-coal-heavy-01":
                    util = 80.0 + random.uniform(-10, 10)
                    mem = 90.0 + random.uniform(-2, 2)
                    power = 1600.0 + (util / 100.0) * 1400.0
                    temp = 72.0 + random.uniform(-3, 3)

                else: # aws-us-east-1-a100-idle
                    util = 3.0 + random.uniform(-1, 2)
                    mem = 10.0 + random.uniform(-1, 1)
                    power = 400.0 + (util / 100.0) * 800.0
                    temp = 48.0 + (util / 100.0) * 5.0

                # Write Utilization Log
                util_log = GPUUtilizationLog(
                    node_id=node.id,
                    timestamp=current_time,
                    gpu_utilization_pct=round(util, 2),
                    memory_utilization_pct=round(mem, 2),
                    power_draw_watts=round(power, 2),
                    temperature_c=round(temp, 1)
                )
                db.add(util_log)

                # Write Carbon Log
                energy_kwh = (power / 1000.0) * 1.0
                carbon_g = energy_kwh * node.carbon_intensity
                carbon_log = CarbonEmissionsLog(
                    node_id=node.id,
                    timestamp=current_time,
                    energy_consumed_kwh=round(energy_kwh, 4),
                    carbon_emitted_grams=round(carbon_g, 2)
                )
                db.add(carbon_log)

            for dep in deployments:
                node = next(n for n in nodes if n.id == dep.node_id)
                requests_count = int(dep.target_tps * 3600 * (traffic_multiplier / 1.0))
                for _ in range(3):
                    latency_mult = 1.0
                    if is_peak and dep.id == "llama-3-70b":
                        latency_mult = random.uniform(1.1, 1.4)
                    
                    base_lat = dep.sla_latency_ms * random.uniform(0.7, 0.9)
                    lat = base_lat * latency_mult
                    
                    if random.random() < 0.05:
                        lat *= 1.8
                    
                    prompt = random.choice([256, 512, 1024, 2048])
                    completion = random.choice([64, 128, 256, 512])
                    
                    error = random.random() < 0.01
                    sla_violation = (lat > dep.sla_latency_ms) and not error

                    req_log = InferenceRequestLog(
                        model_id=dep.id,
                        timestamp=current_time + datetime.timedelta(minutes=random.randint(0, 59)),
                        prompt_tokens=prompt,
                        completion_tokens=completion,
                        latency_ms=round(lat, 2),
                        error_occurred=error,
                        sla_violation=sla_violation
                    )
                    db.add(req_log)

            current_time += datetime.timedelta(hours=1)

        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend root to path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base
from app.models import (
    User, UserActivityLog, GPUClusterNode, ModelDeployment, 
    GPUUtilizationLog, InferenceRequestLog, CarbonEmissionsLog
)

def migrate():
    load_dotenv()
    
    sqlite_url = "sqlite:///./aether_gpu_finops.db"
    mysql_url = os.getenv("DATABASE_URL")
    
    if not mysql_url or "mysql" not in mysql_url:
        print("ERROR: DATABASE_URL env var is not set to a MySQL connection string!")
        sys.exit(1)
        
    print(f"Starting database migration...")
    print(f"Source (SQLite): {sqlite_url}")
    print(f"Destination (MySQL): {mysql_url}")
    
    sqlite_engine = create_engine(sqlite_url)
    mysql_engine = create_engine(mysql_url)
    
    # 1. Recreate MySQL Schema
    print("\nDropping existing MySQL tables...")
    Base.metadata.drop_all(bind=mysql_engine)
    print("Recreating MySQL tables...")
    Base.metadata.create_all(bind=mysql_engine)
    
    # Sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    MysqlSession = sessionmaker(bind=mysql_engine)
    
    sqlite_session = SqliteSession()
    mysql_session = MysqlSession()
    
    try:
        # Copy tables in dependency order
        
        # 1. Users
        print("\nMigrating table 'users'...")
        users = sqlite_session.query(User).all()
        for u in users:
            # Create a new instance to detach from sqlite session
            mysql_session.add(User(
                id=u.id,
                email=u.email,
                hashed_password=u.hashed_password,
                role=u.role
            ))
        mysql_session.commit()
        print(f"Migrated {len(users)} users.")
        
        # 2. UserActivityLog
        print("Migrating table 'user_activity_logs'...")
        activity_logs = sqlite_session.query(UserActivityLog).all()
        for l in activity_logs:
            mysql_session.add(UserActivityLog(
                id=l.id,
                timestamp=l.timestamp,
                username=l.username,
                action=l.action,
                ip_address=l.ip_address
            ))
        mysql_session.commit()
        print(f"Migrated {len(activity_logs)} activity logs.")
        
        # 3. GPUClusterNode
        print("Migrating table 'gpu_cluster_nodes'...")
        nodes = sqlite_session.query(GPUClusterNode).all()
        for n in nodes:
            mysql_session.add(GPUClusterNode(
                id=n.id,
                provider=n.provider,
                region=n.region,
                gpu_type=n.gpu_type,
                gpu_count=n.gpu_count,
                hourly_cost=n.hourly_cost,
                carbon_intensity=n.carbon_intensity,
                status=n.status
            ))
        mysql_session.commit()
        print(f"Migrated {len(nodes)} cluster nodes.")
        
        # 4. ModelDeployment
        print("Migrating table 'model_deployments'...")
        deployments = sqlite_session.query(ModelDeployment).all()
        for d in deployments:
            mysql_session.add(ModelDeployment(
                id=d.id,
                name=d.name,
                node_id=d.node_id,
                gpu_allocated=d.gpu_allocated,
                sla_latency_ms=d.sla_latency_ms,
                target_tps=d.target_tps
            ))
        mysql_session.commit()
        print(f"Migrated {len(deployments)} deployments.")
        
        # 5. GPUUtilizationLog
        print("Migrating table 'gpu_utilization_logs'...")
        util_logs = sqlite_session.query(GPUUtilizationLog).all()
        for l in util_logs:
            mysql_session.add(GPUUtilizationLog(
                id=l.id,
                node_id=l.node_id,
                timestamp=l.timestamp,
                gpu_utilization_pct=l.gpu_utilization_pct,
                memory_utilization_pct=l.memory_utilization_pct,
                power_draw_watts=l.power_draw_watts,
                temperature_c=l.temperature_c
            ))
        mysql_session.commit()
        print(f"Migrated {len(util_logs)} utilization logs.")
        
        # 6. InferenceRequestLog
        print("Migrating table 'inference_request_logs'...")
        inference_logs = sqlite_session.query(InferenceRequestLog).all()
        for l in inference_logs:
            mysql_session.add(InferenceRequestLog(
                id=l.id,
                model_id=l.model_id,
                timestamp=l.timestamp,
                prompt_tokens=l.prompt_tokens,
                completion_tokens=l.completion_tokens,
                latency_ms=l.latency_ms,
                error_occurred=l.error_occurred,
                sla_violation=l.sla_violation
            ))
        mysql_session.commit()
        print(f"Migrated {len(inference_logs)} inference logs.")
        
        # 7. CarbonEmissionsLog
        print("Migrating table 'carbon_emissions_logs'...")
        carbon_logs = sqlite_session.query(CarbonEmissionsLog).all()
        for l in carbon_logs:
            mysql_session.add(CarbonEmissionsLog(
                id=l.id,
                node_id=l.node_id,
                timestamp=l.timestamp,
                energy_consumed_kwh=l.energy_consumed_kwh,
                carbon_emitted_grams=l.carbon_emitted_grams
            ))
        mysql_session.commit()
        print(f"Migrated {len(carbon_logs)} carbon logs.")
        
        print("\nDATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        mysql_session.rollback()
        print(f"ERROR migrating data: {e}")
        sys.exit(1)
    finally:
        sqlite_session.close()
        mysql_session.close()

if __name__ == "__main__":
    migrate()

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="User")  # Admin, User

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    username = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)   # "login", "simulate", "export", etc.
    ip_address = Column(String(50), nullable=True)

class GPUClusterNode(Base):
    __tablename__ = "gpu_cluster_nodes"

    id = Column(String(255), primary_key=True, index=True)
    provider = Column(String(50), nullable=False)         # AWS, GCP, On-Prem
    region = Column(String(100), nullable=False)           # us-east-1, us-central1, private-dc
    gpu_type = Column(String(100), nullable=False)         # H100, A100, L4
    gpu_count = Column(Integer, nullable=False)       # 8, 4, 1 etc.
    hourly_cost = Column(Float, nullable=False)       # Node hourly cost in USD
    carbon_intensity = Column(Float, nullable=False)  # g CO2 per kWh of grid energy
    status = Column(String(50), default="Active")         # Active, Maintenance, Idle

    utilization_logs = relationship("GPUUtilizationLog", back_populates="node")
    deployments = relationship("ModelDeployment", back_populates="node")
    emissions_logs = relationship("CarbonEmissionsLog", back_populates="node")

class ModelDeployment(Base):
    __tablename__ = "model_deployments"

    id = Column(String(255), primary_key=True, index=True) # e.g. llama-3-70b-service
    name = Column(String(255), nullable=False)             # Llama-3-70B-Instruct
    node_id = Column(String(255), ForeignKey("gpu_cluster_nodes.id"), nullable=False)
    gpu_allocated = Column(Integer, nullable=False)   # Number of GPUs allocated
    sla_latency_ms = Column(Integer, nullable=False)  # SLA target latency in ms
    target_tps = Column(Float, nullable=False)        # Target transactions per second

    node = relationship("GPUClusterNode", back_populates="deployments")
    inference_logs = relationship("InferenceRequestLog", back_populates="model")

class GPUUtilizationLog(Base):
    __tablename__ = "gpu_utilization_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_id = Column(String(255), ForeignKey("gpu_cluster_nodes.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    gpu_utilization_pct = Column(Float, nullable=False)
    memory_utilization_pct = Column(Float, nullable=False)
    power_draw_watts = Column(Float, nullable=False)  # Node level power consumption
    temperature_c = Column(Float, nullable=False)

    node = relationship("GPUClusterNode", back_populates="utilization_logs")

class InferenceRequestLog(Base):
    __tablename__ = "inference_request_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(String(255), ForeignKey("model_deployments.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    error_occurred = Column(Boolean, default=False)
    sla_violation = Column(Boolean, default=False)

    model = relationship("ModelDeployment", back_populates="inference_logs")

class CarbonEmissionsLog(Base):
    __tablename__ = "carbon_emissions_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_id = Column(String(255), ForeignKey("gpu_cluster_nodes.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    energy_consumed_kwh = Column(Float, nullable=False)  # Node level energy consumed (kWh)
    carbon_emitted_grams = Column(Float, nullable=False) # Energy * Grid Carbon Intensity

    node = relationship("GPUClusterNode", back_populates="emissions_logs")


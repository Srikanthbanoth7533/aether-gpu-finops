from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

# Base Schemas
class GPUClusterNodeBase(BaseModel):
    id: str
    provider: str
    region: str
    gpu_type: str
    gpu_count: int
    hourly_cost: float
    carbon_intensity: float
    status: str

    class Config:
        from_attributes = True

class ModelDeploymentBase(BaseModel):
    id: str
    name: str
    node_id: str
    gpu_allocated: int
    sla_latency_ms: int
    target_tps: float

    class Config:
        from_attributes = True

# Custom Analytics Schemas
class KPIOverview(BaseModel):
    total_spend_usd: float
    gpu_idle_cost_penalty_usd: float  # GICP: Cost of underutilized resources (avg <15% utilization)
    gpu_idle_cost_penalty_pct: float
    avg_model_compute_efficiency: float # MCES: total tokens / Wh consumed
    sla_violation_exposure_index: float # SLA-VEI: penalty-weighted SLA breach percentage
    total_carbon_emitted_kg: float
    carbon_offset_roi: float           # COROI: Ratio of offset cost to carbon emissions avoided

class TimelineDataPoint(BaseModel):
    timestamp: str
    gpu_utilization_pct: float
    power_draw_watts: float
    hourly_cost_usd: float
    carbon_emitted_kg: float

class ModelEfficiencyDataPoint(BaseModel):
    model_id: str
    model_name: str
    tokens_per_watt_hour: float
    avg_latency_ms: float
    sla_violation_pct: float

class ProviderMetrics(BaseModel):
    provider: str
    total_spend_usd: float
    carbon_emitted_kg: float
    avg_utilization_pct: float

# What-if Simulation Schemas
class SimulatorInput(BaseModel):
    node_id: str
    gpu_count_multiplier: float      # Scale nodes by 0.5x, 1x, 2x, etc.
    active_hours_per_day: float       # Scale operations time
    target_model_concurrency: float  # Expected traffic multiplier
    routing_strategy: str             # "default", "cost-optimized", "carbon-optimized"

class SimulatorResult(BaseModel):
    current_cost_usd: float
    projected_cost_usd: float
    current_carbon_kg: float
    projected_carbon_kg: float
    current_sla_violation_pct: float
    projected_sla_violation_pct: float
    monthly_savings_usd: float
    net_carbon_saved_kg: float

# AI Advisor Schemas
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    response: str
    suggested_actions: List[Dict[str, str]]

# User Authentication & Enterprise Logs Schemas
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    role: Optional[str] = "User" # "Admin" or "User"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    email: str
    role: str

class UserResponse(BaseModel):
    email: str
    role: str

class ActivityLogSchema(BaseModel):
    id: int
    timestamp: datetime
    username: str
    action: str
    ip_address: Optional[str]

    class Config:
        from_attributes = True

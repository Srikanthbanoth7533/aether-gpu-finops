from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class SQLQueryRequest(BaseModel):
    query: str

class SQLQueryResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    execution_time_ms: float
    error: Optional[str] = None

class KPIResponse(BaseModel):
    total_revenue: float
    total_profit: float
    profit_margin: float
    average_order_value: float
    conversion_rate: float
    repeat_customer_rate: float
    total_orders: int
    total_customers: int

class TrendPoint(BaseModel):
    date: str
    sales: float
    profit: float
    orders: int

class CategoryProfitability(BaseModel):
    category: str
    sub_category: Optional[str] = None
    sales: float
    profit: float
    quantity: int
    profit_margin: float

class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float  # Percentage of initial stage

class TopProductResponse(BaseModel):
    product_id: str
    name: str
    category: str
    sales: float
    profit: float
    quantity_sold: int

class Recommendation(BaseModel):
    id: int
    category: str
    title: str
    description: str
    impact: str  # High, Medium, Low
    estimated_val: float

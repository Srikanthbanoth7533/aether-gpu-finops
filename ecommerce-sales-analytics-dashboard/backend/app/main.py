from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .database import get_db, engine, Base
from . import crud, schemas

app = FastAPI(
    title="E-commerce Sales Analytics Dashboard API",
    description="API for E-commerce KPIs, Sales Trends, Cohort Analysis, and Safe SQL Console",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domain
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

@app.on_event("startup")
def startup_db():
    # Automatically create tables if they don't exist
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "E-commerce Sales Analytics API",
        "docs": "/docs"
    }

@app.post("/api/seed", status_code=200)
def trigger_seed():
    """
    Triggers database seeding. Handy for refreshing the data.
    """
    try:
        from data.seed_data import seed_database
        seed_database()
        return {"status": "success", "message": "Database seeded successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed database: {str(e)}")

@app.get("/api/kpis", response_model=schemas.KPIResponse)
def get_kpis(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    segment: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        return crud.get_kpis(db, start_date, end_date, segment, category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends", response_model=List[schemas.TrendPoint])
def get_trends(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    segment: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        return crud.get_trends(db, start_date, end_date, segment, category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories", response_model=List[schemas.CategoryProfitability])
def get_categories(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    segment: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        return crud.get_categories(db, start_date, end_date, segment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/top", response_model=List[schemas.TopProductResponse])
def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        return crud.get_top_products(db, limit, category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funnel", response_model=List[schemas.FunnelStage])
def get_funnel(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        return crud.get_funnel(db, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cohorts")
def get_cohorts(db: Session = Depends(get_db)):
    try:
        return crud.get_cohorts(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=schemas.SQLQueryResponse)
def execute_query(payload: schemas.SQLQueryRequest, db: Session = Depends(get_db)):
    try:
        result = crud.execute_safe_sql(db, payload.query)
        if result.get("error"):
            # We don't raise 500/400 because query syntax errors should be returned
            # in the response body's 'error' field so the SQL console can display it.
            pass
        return result
    except Exception as e:
        return {
            "columns": [],
            "rows": [],
            "execution_time_ms": 0.0,
            "error": str(e)
        }

@app.get("/api/recommendations", response_model=List[schemas.Recommendation])
def get_recommendations(db: Session = Depends(get_db)):
    try:
        return crud.get_recommendations(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

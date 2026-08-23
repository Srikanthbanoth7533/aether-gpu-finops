import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aether_gpu_finops.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


# Try connecting to DATABASE_URL; fallback to local SQLite if PostgreSQL connection fails or times out
try:
    if DATABASE_URL.startswith("sqlite"):
        engine_args = {
            "connect_args": {"check_same_thread": False},
            "poolclass": NullPool
        }
    else:
        engine_args = {
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 3}
        }
    engine = create_engine(DATABASE_URL, **engine_args)
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"Warning: Database connection failed ({e}). Falling back to pre-seeded SQLite database.")
    DATABASE_URL = "sqlite:///./aether_gpu_finops.db"
    engine_args = {
        "connect_args": {"check_same_thread": False},
        "poolclass": NullPool
    }
    engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


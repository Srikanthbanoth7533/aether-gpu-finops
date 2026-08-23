import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Load environment variables
load_dotenv()

# Determine absolute path to aether_gpu_finops.db
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
db_path = os.path.join(backend_dir, "aether_gpu_finops.db")

if not os.path.exists(db_path):
    parent_db_path = os.path.join(os.path.dirname(backend_dir), "aether_gpu_finops.db")
    if os.path.exists(parent_db_path):
        db_path = parent_db_path

DATABASE_URL = f"sqlite:///{db_path}"

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


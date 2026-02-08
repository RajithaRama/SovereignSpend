from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_path():
    """Get the database path based on environment"""
    env = os.getenv("DB_ENV", "production")
    if env == "testing":
        return "./finance_tracker_test.db"
    elif env == "debug":
        return "./finance_tracker_debug.db"
    return os.getenv("DATABASE_PATH", "./finance_tracker.db")

DATABASE_PATH = get_db_path()
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from backend.models import Account, Transaction, Transfer, Invoice, BankStatement
    Base.metadata.create_all(bind=engine)

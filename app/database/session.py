import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment or .env file.")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    # pool_pre_ping=True helps detect and recover from dropped connections automatically
    pool_pre_ping=True
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative Base for ORM models
Base = declarative_base()

# Dependency to get db session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

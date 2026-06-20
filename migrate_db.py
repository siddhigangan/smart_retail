"""
One-time DB migration script.
Run: python migrate_db.py
Adds customers table and new columns to bills table.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

migrations = [
    # Create customers table
    """
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        phone VARCHAR(15) UNIQUE NOT NULL,
        email VARCHAR(255),
        total_points INTEGER DEFAULT 0 NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    # Index on phone for fast lookups
    "CREATE INDEX IF NOT EXISTS ix_customers_phone ON customers(phone);",
    # Add new columns to bills
    "ALTER TABLE bills ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL;",
    "ALTER TABLE bills ADD COLUMN IF NOT EXISTS customer_name VARCHAR(100);",
    "ALTER TABLE bills ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(15);",
    "ALTER TABLE bills ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255);",
]

with engine.connect() as conn:
    for sql in migrations:
        conn.execute(text(sql))
        print(f"[OK] Executed: {sql.strip()[:60]}...")
    conn.commit()

print("\n[DONE] Migration complete.")

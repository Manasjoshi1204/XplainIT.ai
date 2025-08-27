import os
import databases
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse

# Database URL configuration
def get_database_url():
    """Get database URL based on environment"""
    if os.getenv("DATABASE_URL"):  # Render PostgreSQL
        url = os.getenv("DATABASE_URL")
        # Fix for Render's postgres:// vs postgresql:// issue
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    else:  # Local development - fallback to SQLite
        return "sqlite:///./xplainit.db"

DATABASE_URL = get_database_url()
print(f"🗃️ Database URL: {DATABASE_URL}")

# Check if using PostgreSQL or SQLite
IS_POSTGRES = DATABASE_URL.startswith("postgresql://")
IS_SQLITE = DATABASE_URL.startswith("sqlite://")

print(f"📊 Using {'PostgreSQL' if IS_POSTGRES else 'SQLite'} database")

# Create database connection
if IS_POSTGRES:
    database = databases.Database(DATABASE_URL)
    engine = create_engine(DATABASE_URL)
else:
    # For SQLite, use synchronous connection
    database = None
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

metadata = MetaData()
Base = declarative_base()

# Define Users table
users_table = Table(
    "users",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("username", String, unique=True, nullable=False, index=True),
    Column("email", String, unique=True, nullable=False, index=True),
    Column("hashed_password", String, nullable=False),
    Column("full_name", String),
    Column("total_explanations", Integer, default=0),
    Column("created_at", DateTime, nullable=False),
    Column("is_active", Boolean, default=True)
)

# Define Explanations table
explanations_table = Table(
    "explanations",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("user_id", String, ForeignKey("users.id"), nullable=False),
    Column("topic", String, nullable=False),
    Column("explanation", Text, nullable=False),
    Column("level", String),
    Column("tone", String),
    Column("language", String),
    Column("extras", String),
    Column("timestamp", DateTime, nullable=False)
)

# Create SessionLocal for SQLite fallback
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database connection functions
async def connect_database():
    """Connect to database"""
    if IS_POSTGRES and database:
        await database.connect()
        print("✅ Connected to PostgreSQL database")
    else:
        print("✅ Using SQLite database")

async def disconnect_database():
    """Disconnect from database"""
    if IS_POSTGRES and database:
        await database.disconnect()
        print("🔌 Disconnected from PostgreSQL database")

def create_tables():
    """Create all tables"""
    try:
        metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

# Database operation functions
def get_db():
    """Get database session for SQLite"""
    if IS_SQLITE:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        # For PostgreSQL, we'll use the databases library directly
        yield None

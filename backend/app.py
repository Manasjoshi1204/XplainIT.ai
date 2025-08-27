# Enhanced backend/app.py with PostgreSQL and SQLite support
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uvicorn
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os
import sys
import json
import traceback
import asyncio
import sqlite3

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from explain_engine import generate_explanation

# Import database configuration
from database import (
    DATABASE_URL, IS_POSTGRES, IS_SQLITE, database, engine, metadata,
    users_table, explanations_table, connect_database, disconnect_database,
    create_tables, get_db
)

# JWT Configuration
SECRET_KEY = "hjvhvjn,hcsvaeukfhbaukshfbahkv-0-48724"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="XplainIT.ai Backend", version="2.0.0", debug=True)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "https://xplainit-ai-frontend.onrender.com",
        "https://xplainit-ai-frontend.onrender.com/",
        "*"  # Be more restrictive in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Data Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    total_explanations: int = 0
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class ExplanationRequest(BaseModel):
    topic: str
    level: str = "Beginner"
    tone: str = "Casual"
    extras: str = ""
    language: str = "English"

class ExplanationResponse(BaseModel):
    id: str
    explanation: str
    topic: str
    timestamp: datetime
    settings: dict

# Database functions for PostgreSQL
async def get_user_by_username_pg(username: str):
    """Get user from PostgreSQL database by username"""
    try:
        query = users_table.select().where(users_table.c.username == username)
        result = await database.fetch_one(query)
        return dict(result) if result else None
    except Exception as e:
        print(f"❌ Error getting user {username}: {e}")
        return None

async def get_user_by_email_pg(email: str):
    """Get user from PostgreSQL database by email"""
    try:
        query = users_table.select().where(users_table.c.email == email)
        result = await database.fetch_one(query)
        return dict(result) if result else None
    except Exception as e:
        print(f"❌ Error getting user by email {email}: {e}")
        return None

async def create_user_in_db_pg(user_data: dict):
    """Create user in PostgreSQL database"""
    try:
        query = users_table.insert().values(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=user_data["hashed_password"],
            full_name=user_data["full_name"],
            created_at=user_data["created_at"],
            total_explanations=0,
            is_active=True
        )
        await database.execute(query)
        print(f"✅ User {user_data['username']} created successfully in PostgreSQL!")
    except Exception as e:
        print(f"❌ Error creating user in PostgreSQL: {e}")
        raise

async def save_explanation_to_db_pg(explanation_data: dict):
    """Save explanation to PostgreSQL database"""
    try:
        # Insert explanation
        query = explanations_table.insert().values(
            id=explanation_data["id"],
            user_id=explanation_data["user_id"],
            topic=explanation_data["topic"],
            explanation=explanation_data["explanation"],
            level=explanation_data["settings"]["level"],
            tone=explanation_data["settings"]["tone"],
            language=explanation_data["settings"]["language"],
            extras=explanation_data["settings"]["extras"],
            timestamp=explanation_data["timestamp"]
        )
        await database.execute(query)
        
        # Update user's total explanations
        update_query = users_table.update().where(
            users_table.c.id == explanation_data["user_id"]
        ).values(
            total_explanations=users_table.c.total_explanations + 1
        )
        await database.execute(update_query)
        
        print(f"✅ Explanation saved for user {explanation_data['user_id']} in PostgreSQL")
    except Exception as e:
        print(f"❌ Error saving explanation to PostgreSQL: {e}")
        raise

async def get_user_explanations_pg(user_id: str):
    """Get user's explanations from PostgreSQL database"""
    try:
        query = explanations_table.select().where(
            explanations_table.c.user_id == user_id
        ).order_by(explanations_table.c.timestamp.desc()).limit(20)
        
        results = await database.fetch_all(query)
        return [dict(exp) for exp in results]
    except Exception as e:
        print(f"❌ Error getting explanations for user {user_id}: {e}")
        return []

# Database functions for SQLite (fallback)
def get_user_by_username_sqlite(username: str):
    """Get user from SQLite database by username"""
    try:
        conn = sqlite3.connect("xplainit.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    except Exception as e:
        print(f"❌ Error getting user {username} from SQLite: {e}")
        return None

def get_user_by_email_sqlite(email: str):
    """Get user from SQLite database by email"""
    try:
        conn = sqlite3.connect("xplainit.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    except Exception as e:
        print(f"❌ Error getting user by email {email} from SQLite: {e}")
        return None

def create_user_in_db_sqlite(user_data: dict):
    """Create user in SQLite database"""
    try:
        conn = sqlite3.connect("xplainit.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                total_explanations INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            INSERT INTO users (id, username, email, hashed_password, full_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_data["id"],
            user_data["username"], 
            user_data["email"],
            user_data["hashed_password"],
            user_data["full_name"],
            user_data["created_at"].isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ User {user_data['username']} created successfully in SQLite!")
        
    except Exception as e:
        print(f"❌ Error creating user in SQLite: {e}")
        raise

# Wrapper functions to handle both databases
async def get_user_by_username(username: str):
    """Get user by username - handles both PostgreSQL and SQLite"""
    if IS_POSTGRES:
        return await get_user_by_username_pg(username)
    else:
        return get_user_by_username_sqlite(username)

async def get_user_by_email(email: str):
    """Get user by email - handles both PostgreSQL and SQLite"""
    if IS_POSTGRES:
        return await get_user_by_email_pg(email)
    else:
        return get_user_by_email_sqlite(email)

async def create_user_in_db(user_data: dict):
    """Create user in database - handles both PostgreSQL and SQLite"""
    if IS_POSTGRES:
        await create_user_in_db_pg(user_data)
    else:
        create_user_in_db_sqlite(user_data)

async def save_explanation_to_db(explanation_data: dict):
    """Save explanation to database - handles both PostgreSQL and SQLite"""
    if IS_POSTGRES:
        await save_explanation_to_db_pg(explanation_data)
    else:
        # SQLite implementation (similar to your existing code)
        pass

async def get_user_explanations(user_id: str):
    """Get user explanations - handles both PostgreSQL and SQLite"""
    if IS_POSTGRES:
        return await get_user_explanations_pg(user_id)
    else:
        # SQLite implementation
        return []

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Initialize database connection and create tables"""
    print(f"🚀 Starting XplainIT.ai Backend (Database: {'PostgreSQL' if IS_POSTGRES else 'SQLite'})")
    
    if IS_POSTGRES:
        await connect_database()
    
    # Create tables
    create_tables()
    
    print("✅ Application startup completed!")

@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    if IS_POSTGRES:
        await disconnect_database()
    print("🔌 Application shutdown completed!")

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def authenticate_user(username: str, password: str):
    user = await get_user_by_username(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "🧠 XplainIT.ai Backend API",
        "status": "running",
        "version": "2.0.0",
        "database": "PostgreSQL" if IS_POSTGRES else "SQLite",
        "database_url": DATABASE_URL.split('@')[0] + '@***' if '@' in DATABASE_URL else DATABASE_URL,
        "environment": "production" if os.getenv("RENDER") else "local",
        "features": ["Authentication", "Database Storage", "AI Explanations", "History Tracking", "User Management"]
    }

@app.post("/auth/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    """Register a new user"""
    print(f"🔍 Signup attempt for username: {user.username}, email: {user.email}")
    
    # Check if username exists
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        print(f"❌ Username {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    existing_email = await get_user_by_email(user.email)
    if existing_email:
        print(f"❌ Email {user.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = f"user_{int(datetime.utcnow().timestamp())}"
    hashed_password = get_password_hash(user.password)
    
    new_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "total_explanations": 0,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    try:
        await create_user_in_db(new_user)
        print(f"✅ User {user.username} created successfully")
        return UserResponse(**new_user)
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return access token"""
    print(f"🔍 Login attempt for username: {form_data.username}")
    
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        print(f"❌ Login failed for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ Login successful for username: {form_data.username}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        total_explanations=current_user["total_explanations"],
        created_at=datetime.fromisoformat(current_user["created_at"]) if isinstance(current_user["created_at"], str) else current_user["created_at"]
    )

@app.post("/api/explain", response_model=ExplanationResponse)
async def explain_topic(request: ExplanationRequest, current_user: dict = Depends(get_current_user)):
    """Generate AI explanation for authenticated user"""
    try:
        # Generate explanation
        explanation = generate_explanation(
            request.topic, 
            request.level, 
            request.tone, 
            request.extras, 
            request.language
        )
        
        # Create explanation record
        explanation_id = f"exp_{int(datetime.utcnow().timestamp())}"
        explanation_data = {
            "id": explanation_id,
            "user_id": current_user["id"],
            "explanation": explanation,
            "topic": request.topic,
            "timestamp": datetime.utcnow(),
            "settings": {
                "level": request.level,
                "tone": request.tone,
                "language": request.language,
                "extras": request.extras
            }
        }
        
        # Save to database
        await save_explanation_to_db(explanation_data)
        
        return ExplanationResponse(**explanation_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@app.get("/api/history")
async def get_user_history(current_user: dict = Depends(get_current_user)):
    """Get explanation history for current user"""
    explanations = await get_user_explanations(current_user["id"])
    return {
        "user_id": current_user["id"],
        "username": current_user["username"],
        "explanations": explanations,
        "total_count": len(explanations)
    }

@app.get("/debug/db-info")
async def debug_database_info():
    """Debug endpoint to check database status"""
    try:
        if IS_POSTGRES:
            # PostgreSQL info
            query = "SELECT COUNT(*) FROM users"
            user_count = await database.fetch_val(query)
            
            return {
                "database_type": "PostgreSQL",
                "database_url": DATABASE_URL.split('@')[0] + '@***' if '@' in DATABASE_URL else DATABASE_URL,
                "connection_status": "connected",
                "total_users": user_count,
                "environment": "production" if os.getenv("RENDER") else "local"
            }
        else:
            # SQLite info
            return {
                "database_type": "SQLite",
                "database_path": "xplainit.db",
                "connection_status": "connected",
                "environment": "local"
            }
    except Exception as e:
        return {
            "error": str(e),
            "database_type": "PostgreSQL" if IS_POSTGRES else "SQLite",
            "connection_status": "error"
        }

@app.get("/test")
def test_connection():
    return {
        "test": "✅ Backend connection successful!",
        "database": "PostgreSQL" if IS_POSTGRES else "SQLite",
        "environment": "production" if os.getenv("RENDER") else "local",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

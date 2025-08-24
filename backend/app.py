# Enhanced backend/app.py with SQLite Database - FULLY CORRECTED VERSION
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uvicorn
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import sqlite3
import os
import sys
import json
import traceback

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from explain_engine import generate_explanation

# JWT Configuration
SECRET_KEY = "your-super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="XplainIT.ai Backend", version="1.0.0", debug=True)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
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

# Database functions
def init_database():
    """Initialize SQLite database"""
    try:
        print("🔍 Initializing database...")
        conn = sqlite3.connect('xplainit.db')
        cursor = conn.cursor()
        
        # Users table
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
        
        # Explanations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS explanations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                explanation TEXT NOT NULL,
                level TEXT,
                tone TEXT,
                language TEXT,
                extras TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

def get_user_by_username(username: str):
    """Get user from database by username"""
    try:
        conn = sqlite3.connect('xplainit.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    except Exception as e:
        print(f"❌ Error getting user {username}: {e}")
        return None

def create_user_in_db(user_data: dict):
    """Create user in database"""
    try:
        conn = sqlite3.connect('xplainit.db')
        cursor = conn.cursor()
        
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
        print(f"✅ User {user_data['username']} created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise

def save_explanation_to_db(explanation_data: dict):
    """Save explanation to database"""
    try:
        conn = sqlite3.connect('xplainit.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO explanations (id, user_id, topic, explanation, level, tone, language, extras, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            explanation_data["id"],
            explanation_data["user_id"],
            explanation_data["topic"],
            explanation_data["explanation"],
            explanation_data["settings"]["level"],
            explanation_data["settings"]["tone"],
            explanation_data["settings"]["language"],
            explanation_data["settings"]["extras"],
            explanation_data["timestamp"].isoformat()
        ))
        
        # Update user's total explanations
        cursor.execute('''
            UPDATE users SET total_explanations = total_explanations + 1 
            WHERE id = ?
        ''', (explanation_data["user_id"],))
        
        conn.commit()
        conn.close()
        print(f"✅ Explanation saved for user {explanation_data['user_id']}")
        
    except Exception as e:
        print(f"❌ Error saving explanation: {e}")
        raise

def get_user_explanations(user_id: str):
    """Get user's explanations from database"""
    try:
        conn = sqlite3.connect('xplainit.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM explanations WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT 20
        ''', (user_id,))
        
        explanations = cursor.fetchall()
        conn.close()
        
        return [dict(exp) for exp in explanations]
    except Exception as e:
        print(f"❌ Error getting explanations for user {user_id}: {e}")
        return []

def get_platform_stats():
    """Get platform statistics"""
    try:
        conn = sqlite3.connect('xplainit.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM explanations')
        total_explanations = cursor.fetchone()[0]
        
        cursor.execute('SELECT topic FROM explanations ORDER BY timestamp DESC LIMIT 5')
        recent_topics = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_users": total_users,
            "total_explanations": total_explanations,
            "recent_topics": recent_topics
        }
    except Exception as e:
        print(f"❌ Error getting platform stats: {e}")
        return {"total_users": 0, "total_explanations": 0, "recent_topics": []}

# Initialize database on startup
init_database()

# Check database status
print("🔍 Checking database status...")
if os.path.exists('xplainit.db'):
    print("✅ Database file exists!")
    try:
        conn = sqlite3.connect('xplainit.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Tables found: {[table[0] for table in tables]}")
        conn.close()
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
else:
    print("❌ Database file missing!")

# Exception handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print("=== GLOBAL EXCEPTION ===")
    print(f"Error: {exc}")
    print(f"Type: {type(exc).__name__}")
    traceback.print_exc()
    print("========================")
    return {"error": str(exc), "type": type(exc).__name__}

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

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
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
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "🧠 XplainIT.ai Backend API",
        "status": "running",
        "version": "1.0.0",
        "features": ["Authentication", "Database Storage", "AI Explanations", "History Tracking", "User Management"],
        "database_status": "connected" if os.path.exists('xplainit.db') else "missing"
    }

@app.post("/auth/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    """Register a new user"""
    # Check if user exists
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
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
    
    create_user_in_db(new_user)
    
    return UserResponse(**new_user)

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return access token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
        created_at=datetime.fromisoformat(current_user["created_at"])
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
        save_explanation_to_db(explanation_data)
        
        return ExplanationResponse(**explanation_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@app.get("/api/history")
async def get_user_history(current_user: dict = Depends(get_current_user)):
    """Get explanation history for current user"""
    explanations = get_user_explanations(current_user["id"])
    return {
        "user_id": current_user["id"],
        "username": current_user["username"],
        "explanations": explanations,
        "total_count": len(explanations)
    }

@app.get("/api/stats")
async def get_stats():
    """Get overall platform statistics"""
    return get_platform_stats()

# Admin endpoints
@app.get("/admin/users")
async def list_all_users():
    """List all users in database (for debugging)"""
    try:
        print("🔍 Listing all users...")
        conn = sqlite3.connect('xplainit.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, email, total_explanations, created_at FROM users')
        users = cursor.fetchall()
        conn.close()
        
        user_list = [
            {
                "username": user[0],
                "email": user[1], 
                "total_explanations": user[2],
                "created_at": user[3]
            }
            for user in users
        ]
        
        print(f"📊 Found {len(user_list)} users")
        return {
            "total_users": len(user_list),
            "users": user_list
        }
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

@app.delete("/admin/users/{username}")
async def delete_user(username: str):
    """Delete user and all their data from database"""
    try:
        print(f"🔍 Attempting to delete user: {username}")
        
        conn = sqlite3.connect('xplainit.db')
        cursor = conn.cursor()
        
        # Check if user exists first
        print("📋 Checking if user exists...")
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            print(f"❌ User {username} not found in database")
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        
        user_id = user[0]
        print(f"✅ Found user with ID: {user_id}")
        
        # Delete user's explanations first
        print("🗑️ Deleting user explanations...")
        cursor.execute('DELETE FROM explanations WHERE user_id = ?', (user_id,))
        deleted_explanations = cursor.rowcount
        print(f"📊 Deleted {deleted_explanations} explanations")
        
        # Delete user
        print("🗑️ Deleting user record...")
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        deleted_users = cursor.rowcount
        print(f"📊 Deleted {deleted_users} user records")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully deleted user {username}")
        return {"message": f"User {username} deleted successfully (removed {deleted_explanations} explanations)"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except sqlite3.Error as e:
        print(f"💾 Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"💥 Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@app.get("/test")
def test_connection():
    return {
        "test": "✅ Backend connection successful!",
        "database": "connected" if os.path.exists('xplainit.db') else "missing",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

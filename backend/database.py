# backend/database.py - Database management
import sqlite3
import json
from datetime import datetime
from typing import List, Optional

class XplainITDatabase:
    def __init__(self, db_path: str = "xplainit.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                total_explanations INTEGER DEFAULT 0,
                preferences TEXT
            )
        ''')
        
        # Explanations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                topic TEXT,
                explanation TEXT,
                level TEXT,
                tone TEXT,
                language TEXT,
                extras TEXT,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_explanation(self, user_id: str, topic: str, explanation: str, 
                        level: str, tone: str, language: str, extras: str):
        """Save an explanation to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert explanation
        cursor.execute('''
            INSERT INTO explanations 
            (user_id, topic, explanation, level, tone, language, extras, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, topic, explanation, level, tone, language, extras, datetime.now().isoformat()))
        
        # Update user stats
        cursor.execute('''
            INSERT OR REPLACE INTO users (id, created_at, total_explanations)
            VALUES (?, COALESCE((SELECT created_at FROM users WHERE id = ?), ?), 
                    COALESCE((SELECT total_explanations FROM users WHERE id = ?), 0) + 1)
        ''', (user_id, user_id, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def get_user_history(self, user_id: str, limit: int = 10):
        """Get user's explanation history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT topic, explanation, level, tone, language, timestamp
            FROM explanations 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "topic": row[0],
                "explanation": row[10],
                "level": row[11], 
                "tone": row[12],
                "language": row,
                "timestamp": row
            }
            for row in results
        ]
    
    def get_stats(self):
        """Get platform statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM explanations')
        total_explanations = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()
        
        cursor.execute('''
            SELECT topic FROM explanations 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        recent_topics = [row for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_explanations": total_explanations,
            "total_users": total_users,
            "recent_topics": recent_topics
        }

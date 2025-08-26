# backend/config.py - Configuration settings
import os
from typing import Optional

class Settings:
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./xplainit.db"
    
    # AI Model Configuration
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60
    
    # CORS Settings
    ALLOWED_ORIGINS: list = [
        "https://xplainit-ai-frontend.onrender.com",
        "http://localhost:8501",  # Streamlit
        "http://localhost:3000",  # React dev server
        "https://your-domain.com"  # Production domain
    ]
    
    # API Keys (load from environment variables)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    
    class Config:
        case_sensitive = True

settings = Settings()

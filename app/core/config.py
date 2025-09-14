import os
from decouple import config
from typing import List

class Settings:
    # Database
    MONGODB_URI: str = config('MONGODB_URI', default='mongodb://localhost:27017')
    DB_NAME: str = config('DB_NAME', default='cetec-asistente')
    
    # Authentication
    JWT_SECRET_KEY: str = config('JWT_SECRET_KEY', default='your-secret-key-here')
    JWT_ALGORITHM: str = config('JWT_ALGORITHM', default='HS256')
    JWT_EXPIRE_MINUTES: int = config('JWT_EXPIRE_MINUTES', default=30, cast=int)
    GOOGLE_CLIENT_ID: str = config('GOOGLE_CLIENT_ID', default='')
    
    # CORS
    FRONTEND_URL: str = config('FRONTEND_URL', default='http://localhost:3000')
    BACKEND_CORS_ORIGINS: List[str] = config(
        'BACKEND_CORS_ORIGINS',
        default='http://localhost:3000,http://localhost:8000',
        cast=lambda v: [i.strip() for i in v.split(',')]
    )
    
    # S3 Configuration
    AWS_ACCESS_KEY_ID: str = config('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_KEY: str = config('AWS_SECRET_KEY', default='')
    AWS_REGION: str = config('AWS_REGION', default='us-east-1')
    S3_BUCKET: str = config('S3_BUCKET', default='cetec-documents')
    
    # A2A Configuration
    A2A_DEFAULT_SERVER_URL: str = config('A2A_DEFAULT_SERVER_URL', default='http://localhost:8001')
    
    # Vector Store
    VECTOR_STORE_URL: str = config('VECTOR_STORE_URL', default='http://localhost:6333')
    
    # Application
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Student Chat + Ingestion API"
    VERSION: str = "1.0.0"
    
    # Environment
    ENVIRONMENT: str = config('ENVIRONMENT', default='development')
    DEBUG: bool = config('DEBUG', default=True, cast=bool)

settings = Settings()

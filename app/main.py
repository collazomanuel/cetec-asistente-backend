from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.routers import (
    meta, auth, subjects, documents, ingestion, 
    chat, a2a, webhooks
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

def create_application() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="FastAPI back-end for a student chat system routed through A2A servers and a teacher-facing ingestion UI.",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(meta.router, prefix=settings.API_V1_STR)
    app.include_router(auth.router, prefix=settings.API_V1_STR)
    app.include_router(subjects.router, prefix=settings.API_V1_STR)
    app.include_router(documents.router, prefix=settings.API_V1_STR)
    app.include_router(ingestion.router, prefix=settings.API_V1_STR)
    app.include_router(chat.router, prefix=settings.API_V1_STR)
    app.include_router(a2a.router, prefix=settings.API_V1_STR)
    app.include_router(webhooks.router, prefix=settings.API_V1_STR)

    return app

app = create_application()

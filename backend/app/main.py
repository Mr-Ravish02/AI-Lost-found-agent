import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
import app.models  # Ensures all models are registered
from app.routers import (
    auth_router,
    items_router,
    matching_router,
    verification_router,
    workflow_router,
    admin_router,
    notifications_router
)

# Create database tables automatically on startup
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI-Powered Smart Lost & Found Management System API",
    version="1.0.0"
)

# Configure CORS
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth_router)
app.include_router(items_router)
app.include_router(matching_router)
app.include_router(verification_router)
app.include_router(workflow_router)
app.include_router(admin_router)
app.include_router(notifications_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to AI-Powered Smart Lost & Found Management System API",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

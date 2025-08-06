from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.chat.routes_deepseek import router as deepseek_router

load_dotenv()

# ChatConnect Configuration
app_name = os.getenv("CHATCONNECT_APP_NAME", "ChatConnect")
app_version = os.getenv("CHATCONNECT_VERSION", "1.0.0")
app_description = os.getenv("CHATCONNECT_DESCRIPTION", "AI-Powered MCP Integration Platform with DeepSeek R1")

app = FastAPI(
    title=app_name,
    description=app_description,
    version=app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup for frontend communication
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/chat", tags=["Chat (Legacy)"])
app.include_router(deepseek_router, prefix="/chatconnect", tags=["ChatConnect (DeepSeek R1)"])

@app.get("/")
async def root():
    """Root endpoint with ChatConnect information"""
    return {
        "app": app_name,
        "version": app_version,
        "description": app_description,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "auth": "/auth",
            "chat": "/chat",
            "chatconnect": "/chatconnect"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": app_name,
        "version": app_version
    }

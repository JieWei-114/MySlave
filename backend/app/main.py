"""
Main application entry point
Sets up FastAPI app with CORS, routers, and health checks
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.memory import router as memory_router
from app.api.rules import router as rule_router
from app.api.web import router as web_router
from app.config.settings import settings
from app.core.db import client

# Configure logging level from environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    force=True,
)

# Reduce noisy third-party debug logs
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Initialize FastAPI application
app = FastAPI(title='My Slave', version='1.0.0')

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/')
async def read_root():
    """Root endpoint - welcome message"""
    return {'message': 'Welcome to my API!'}


@app.get('/health')
async def health_check():
    """Health check endpoint with database connectivity status"""
    try:
        # Ping MongoDB to check connection
        client.admin.command('ping')
        db_status = 'connected'
    except Exception:
        db_status = 'disconnected'

    return {
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'database': db_status,
        'version': '1.0.0',
    }


# Register API routers
app.include_router(chat_router)  # Chat sessions and streaming
app.include_router(memory_router)  # Memory management
app.include_router(web_router)  # Web search
app.include_router(rule_router)  # Rules configuration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.memory import router as memory_router
from app.config.settings import settings
from app.core.db import client

app = FastAPI(title='My Slave', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# Add this block to fix the 404 on the root URL
@app.get('/')
async def read_root():
    return {'message': 'Welcome to my API!'}


@app.get('/health')
async def health_check():
    """Health check endpoint with database status"""
    try:
        client.admin.command('ping')
        db_status = 'connected'
    except Exception:
        db_status = 'disconnected'

    return {
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'database': db_status,
        'version': '1.0.0',
    }


app.include_router(chat_router)
app.include_router(memory_router)

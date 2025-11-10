import sys
import os
import logging
import time
from fastapi import Request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from models import init_db
from services.websocket_service import manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Coach API", version="1.0.0")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Входящий запрос: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Запрос {request.method} {request.url.path} выполнен за {process_time:.2f}с, статус: {response.status_code}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["api"])

@app.websocket("/ws/analyze/{call_id}")
async def websocket_analyze(websocket: WebSocket, call_id: int):
    await manager.connect(websocket, call_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, call_id)

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        logger.info("База данных инициализирована")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        manager.set_event_loop(loop)
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise

@app.get("/")
def read_root():
    return {"message": "AI Coach API", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


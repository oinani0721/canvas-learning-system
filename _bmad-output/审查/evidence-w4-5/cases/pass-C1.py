from app.main import app
from fastapi.testclient import TestClient
async def t(lock):
    async with lock:
        pass

import somemod as mod
from app.main import app
from fastapi.testclient import TestClient
def t():
    with mod._refresh_guard:
        pass

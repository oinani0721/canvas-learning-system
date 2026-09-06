from app.main import app
from fastapi.testclient import TestClient
def t(client):
    with client:
        pass

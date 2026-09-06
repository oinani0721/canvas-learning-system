from app.main import app
from fastapi.testclient import TestClient
def t(flag):
    client = TestClient(app)
    with (client if flag else client):
        pass

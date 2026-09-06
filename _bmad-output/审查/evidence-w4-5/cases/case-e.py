import app.main as m
from fastapi.testclient import TestClient
def t():
    c = TestClient(m.app)
    with c:
        pass

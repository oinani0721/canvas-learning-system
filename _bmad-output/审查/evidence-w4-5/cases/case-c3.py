from app.main import app
from fastapi.testclient import TestClient
def make(flag, other):
    if flag:
        return TestClient(app)
    return other
def t(o):
    with make(True, o):
        pass

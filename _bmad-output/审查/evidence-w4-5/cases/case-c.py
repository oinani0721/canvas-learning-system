import contextlib
from app.main import app
from fastapi.testclient import TestClient
def t():
    with contextlib.ExitStack() as s:
        s.enter_context(client := TestClient(app))

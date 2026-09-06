from app.main import app
from fastapi.testclient import TestClient
import contextlib
def t(flag, other):
    with (contextlib.nullcontext() if flag else TestClient(app)):
        pass

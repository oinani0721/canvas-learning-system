import contextlib
from app.main import app
from fastapi.testclient import TestClient
def t(kw):
    with contextlib.ExitStack() as stack:
        c = stack.enter_context(**kw)

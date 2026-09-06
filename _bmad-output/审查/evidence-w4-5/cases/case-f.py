import contextlib
from app.main import app
from fastapi.testclient import TestClient
from tests.support.lifespan import no_lifespan
@contextlib.contextmanager
def isolated(a):
    with no_lifespan(a):
        a = app
        yield a
def t():
    with isolated(app), TestClient(app) as c:
        pass

import contextlib
from app.main import app
from fastapi.testclient import TestClient
from tests.support.lifespan import no_lifespan
@contextlib.contextmanager
def isolated(a, other):
    with no_lifespan(a):
        yield other
def t(o):
    with isolated(app, o), TestClient(app) as c:
        pass

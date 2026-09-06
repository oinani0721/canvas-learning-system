import app.main as m
from fastapi.testclient import TestClient
from tests.support.lifespan import no_lifespan
def t():
    with no_lifespan(m.app), TestClient(m.app) as c:
        pass

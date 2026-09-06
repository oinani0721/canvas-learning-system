from fastapi import FastAPI
from fastapi.testclient import TestClient
def t():
    app = FastAPI()
    del app
    with TestClient(app) as c:
        pass

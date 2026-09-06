from fastapi import FastAPI
from fastapi.testclient import TestClient
import app.main
def make():
    return FastAPI(), TestClient(app.main.app)
def t():
    _, c = make()
    with c:
        pass

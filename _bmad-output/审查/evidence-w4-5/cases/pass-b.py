from fastapi import FastAPI
from fastapi.testclient import TestClient
def t(flag):
    a = FastAPI()
    c1 = TestClient(a)
    c2 = TestClient(a)
    with (c1 if flag else c2):
        pass

import contextlib
from fastapi import FastAPI
from fastapi.testclient import TestClient
def t():
    a = FastAPI()
    with contextlib.ExitStack() as s:
        s.enter_context(cm=TestClient(a))

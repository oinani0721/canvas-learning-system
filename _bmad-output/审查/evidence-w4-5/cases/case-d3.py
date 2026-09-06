from fastapi import FastAPI
from fastapi.testclient import TestClient
def t(x):
    app = FastAPI()
    match x:
        case [app]:
            with TestClient(app) as c:
                pass

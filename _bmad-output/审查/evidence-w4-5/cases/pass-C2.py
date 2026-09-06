import pytest
from app.main import app
from fastapi.testclient import TestClient
def t():
    with pytest.raises(ValueError):
        pass

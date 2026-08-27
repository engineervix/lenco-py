import pytest

BASE_URL = "https://api.lenco.co/access/v2"
TOKEN = "test-token"


@pytest.fixture
def token() -> str:
    return TOKEN

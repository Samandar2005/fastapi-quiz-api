import os
import sys
import pathlib
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def _tmp_db_path():
    tmp_dir = tempfile.mkdtemp(prefix="quiz_api_test_")
    db_file = os.path.join(tmp_dir, "test.db")
    yield db_file
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def app(_tmp_db_path):
    os.environ["DATABASE_URL"] = f"sqlite://{_tmp_db_path}"
    # Ensure project root is on sys.path for module resolution
    project_root = pathlib.Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    # Import after env var is set so main.py registers Tortoise with the test DB
    from main import app as fastapi_app  # type: ignore
    return fastapi_app


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c



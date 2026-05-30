import sys
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

@pytest.fixture
def repo_root():
    return REPO_ROOT

@pytest.fixture
def fixtures_dir():
    return FIXTURES

def read_fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")

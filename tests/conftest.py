import pytest
from app.job import MixingJob
from app.main import create_app
from app.receipts.packet import read_sample

@pytest.fixture(scope='session')
def dirty():
    return MixingJob(read_sample('dirty'))

@pytest.fixture(scope='session')
def clean():
    return MixingJob(read_sample('clean'))

@pytest.fixture
def client(tmp_path):
    return create_app(tmp_path).test_client()

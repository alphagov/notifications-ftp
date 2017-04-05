import pytest
from app import create_app


@pytest.fixture(scope='session')
def notify_ftp():
    app = create_app()

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture(scope='function')
def client(notify_ftp):
    with notify_ftp.test_request_context(), notify_ftp.test_client() as client:
        yield client

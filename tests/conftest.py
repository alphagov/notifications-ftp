import pytest
from app import create_app
import os
from flask import current_app
import shutil
from app.files.file_utils import ensure_local_file_directory


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
        if ensure_local_file_directory():
            shutil.rmtree(current_app.config['LOCAL_FILE_STORAGE_PATH'], ignore_errors=False)

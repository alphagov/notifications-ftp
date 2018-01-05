from datetime import datetime
from flask import current_app
from freezegun import freeze_time
import pytest

from app.celery.tasks import zip_and_send_letter_pdfs
from app.files.file_utils import get_dvla_file_name


@pytest.fixture
def mocks(mocker, client):
    class ZipAndSendLetterPDFsMocks:
        get_zip_of_letter_pdfs_from_s3 = mocker.patch(
            'app.celery.tasks.get_zip_of_letter_pdfs_from_s3',
            return_value=b'\x00\x01'
        )
        upload_to_s3 = mocker.patch('app.celery.tasks.utils_s3upload')
        send_zip = mocker.patch('app.celery.tasks.ftp_client.send_zip')
    with freeze_time('2017-01-01 17:30'):
        yield ZipAndSendLetterPDFsMocks


def test_should_get_zip_of_letter_pdfs_from_s3(mocks):
    filenames = ['2017-01-01/TEST1.PDF', '2017-01-01/TEST2.PDF']

    zip_and_send_letter_pdfs(filenames)

    mocks.get_zip_of_letter_pdfs_from_s3.assert_called_once_with(filenames)


def test_should_upload_zip_of_letter_pdfs_to_s3(notify_ftp, mocks):
    filenames = ['2017-01-01/TEST1.PDF']

    zip_and_send_letter_pdfs(filenames)
    zip_filename = get_dvla_file_name(dt=datetime(2017, 1, 1, 17, 30), file_ext='.zip')
    location = '{}/{}'.format('2017-01-01', zip_filename)
    mocks.upload_to_s3.assert_called_once_with(
        bucket_name=current_app.config['LETTERS_PDF_BUCKET_NAME'],
        file_location=location,
        filedata=b'\x00\x01',
        region='eu-west-1'
    )

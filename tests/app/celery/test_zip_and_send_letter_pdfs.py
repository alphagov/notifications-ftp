from datetime import datetime
from unittest.mock import call

from flask import current_app
from freezegun import freeze_time
import pytest
from botocore.exceptions import ClientError

from app.celery.tasks import zip_and_send_letter_pdfs
from app.files.file_utils import get_dvla_file_name
from app.sftp.ftp_client import FtpException


@pytest.fixture
def mocks(mocker, client):
    class ZipAndSendLetterPDFsMocks:
        get_zip_of_letter_pdfs_from_s3 = mocker.patch(
            'app.celery.tasks.get_zip_of_letter_pdfs_from_s3',
            return_value=b'\x00\x01'
        )
        upload_to_s3 = mocker.patch('app.celery.tasks.utils_s3upload')
        send_zip = mocker.patch('app.celery.tasks.ftp_client.send_zip')
        send_task = mocker.patch('app.notify_celery.send_task')
        get_notification_references_from_s3_filenames = mocker.patch(
            'app.celery.tasks.get_notification_references_from_s3_filenames',
            return_value=['1', '2', '3']
        )

    with freeze_time('2017-01-01 17:30'):
        yield ZipAndSendLetterPDFsMocks


def test_should_get_zip_of_letter_pdfs_from_s3(mocks):
    filenames = ['2017-01-01/TEST1.PDF', '2017-01-01/TEST2.PDF']

    zip_and_send_letter_pdfs(filenames)

    mocks.get_zip_of_letter_pdfs_from_s3.assert_called_once_with(filenames)


def test_should_upload_zip_of_letter_pdfs_to_s3(notify_ftp, mocks):
    filenames = ['2017-01-01/TEST1.PDF']
    zip_filename = get_dvla_file_name(dt=datetime(2017, 1, 1, 17, 30), file_ext='.zip')
    location = '{}/{}'.format('2017-01-01', zip_filename)

    zip_and_send_letter_pdfs(filenames)

    assert mocks.upload_to_s3.call_args_list == [
        call(
            bucket_name=current_app.config['LETTERS_PDF_BUCKET_NAME'],
            file_location='{}/zips_sent/{}.TXT'.format('2017-01-01', zip_filename),
            filedata=b'["2017-01-01/TEST1.PDF"]',
            region='eu-west-1'
        ),
        call(
            bucket_name=current_app.config['LETTERS_PDF_BUCKET_NAME'],
            file_location=location,
            filedata=b'\x00\x01',
            region='eu-west-1'
        )
    ]


def test_should_send_zip_file(mocks):
    filenames = ['2017-01-01/TEST1.PDF']

    zip_and_send_letter_pdfs(filenames)
    zip_filename = get_dvla_file_name(dt=datetime(2017, 1, 1, 17, 30), file_ext='.zip')

    mocks.send_zip.assert_called_once_with(
        b'\x00\x01', zip_filename
    )


def test_should_get_references_out_of_s3_filenames(mocks):
    filenames = ['2017-01-01/TEST1.PDF']

    zip_and_send_letter_pdfs(filenames)

    mocks.get_notification_references_from_s3_filenames.assert_called_once_with(filenames)


def test_zip_and_send_should_update_notifications_to_success(mocks):
    filenames = ['2017-01-01/TEST1.PDF']

    zip_and_send_letter_pdfs(filenames)

    mocks.send_task.assert_called_once_with(
        name='update-letter-notifications-to-sent',
        args=(['1', '2', '3'],),
        queue='notify-internal-tasks'
    )


def test_zip_and_send_should_update_notifications_if_s3_client_error(mocks):
    mocks.get_zip_of_letter_pdfs_from_s3.side_effect = ClientError({}, 'operation')

    filenames = ['2017-01-01/TEST1.PDF']
    zip_and_send_letter_pdfs(filenames)

    mocks.send_task.assert_called_once_with(
        name='update-letter-notifications-to-error',
        args=(['1', '2', '3'],),
        queue='notify-internal-tasks'
    )


def test_zip_and_send_should_update_notifications_if_ftp_error(mocks):
    mocks.send_zip.side_effect = FtpException

    filenames = ['2017-01-01/TEST1.PDF']
    zip_and_send_letter_pdfs(filenames)

    mocks.send_task.assert_called_once_with(
        name='update-letter-notifications-to-error',
        args=(['1', '2', '3'],),
        queue='notify-internal-tasks'
    )


def test_zip_and_send_should_update_notifications_to_success_in_1k_batches(mocker, mocks):
    mocker.patch(
        'app.celery.tasks.get_notification_references_from_s3_filenames',
        return_value=list(range(10000))
    )
    filenames = ['2017-01-01/TEST1.PDF']
    zip_and_send_letter_pdfs(filenames)

    assert mocks.send_task.call_count == 10
    assert mocks.send_task.mock_calls[0][2]['args'] == (list(range(1000)),)
    assert mocks.send_task.mock_calls[1][2]['args'] == (list(range(1000, 2000)),)
    assert mocks.send_task.mock_calls[2][2]['args'] == (list(range(2000, 3000)),)

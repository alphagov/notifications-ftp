import pytest

from app.celery.tasks import send_api_notifications_to_dvla
from app.sftp.ftp_client import FtpException


@pytest.fixture
def mocks(mocker, client):
    class SendApiMocks:
        get_api_from_s3 = mocker.patch('app.celery.tasks.get_api_from_s3')
        rename_api_file = mocker.patch('app.celery.tasks.rename_api_file', return_value='DVLA-FILE')
        send_file = mocker.patch('app.celery.tasks.ftp_client.send_file')
        send_task = mocker.patch('app.notify_celery.send_task')
        get_notification_references = mocker.patch(
            'app.celery.tasks.get_notification_references',
            return_value=['1', '2', '3']
        )
    yield SendApiMocks


def test_should_set_up_local_directory_structure(mocks, mocker):
    localdir = mocker.patch('app.celery.tasks.LocalDir')

    send_api_notifications_to_dvla('')

    localdir.assert_called_once_with('api')


def test_should_get_api_file_from_s3(mocks):
    filename = '2017-01-01T12:34:56Z-dvla-notifications.txt'

    send_api_notifications_to_dvla(filename)

    mocks.get_api_from_s3.assert_called_once_with(filename)


def test_should_rename_api_file(mocks):
    filename = '2017-01-01T12:34:56Z-dvla-notifications.txt'

    send_api_notifications_to_dvla(filename)

    mocks.rename_api_file.assert_called_once_with(filename)


def test_should_send_api_file(mocks):
    send_api_notifications_to_dvla('')

    mocks.send_file.assert_called_once_with("/tmp/dvla-file-storage/api/DVLA-FILE")


def test_should_get_references_out_of_api_file(mocks):
    send_api_notifications_to_dvla('')

    mocks.get_notification_references.assert_called_once_with('DVLA-FILE')


def test_should_update_notifications_to_success(mocks):
    send_api_notifications_to_dvla('')

    mocks.send_task.assert_called_once_with(
        name='update-letter-notifications-to-sent',
        args=(['1', '2', '3'],),
        queue='notify-internal-tasks'
    )


def test_should_update_notifications_if_ftp_error(mocks):
    mocks.send_file.side_effect = FtpException

    send_api_notifications_to_dvla('')

    mocks.send_task.assert_called_once_with(
        name='update-letter-notifications-to-error',
        args=(['1', '2', '3'],),
        queue='notify-internal-tasks'
    )

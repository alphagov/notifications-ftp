from freezegun import freeze_time
import pytest

from app.celery.tasks import send_api_notifications_to_dvla
from app.sftp.ftp_client import FtpException


@pytest.fixture
def mocks(mocker, client):
    class SendApiMocks:
        get_api_from_s3 = mocker.patch('app.celery.tasks.get_api_from_s3')
        send_file = mocker.patch('app.celery.tasks.ftp_client.send_file')
        send_task = mocker.patch('app.notify_celery.send_task')
        get_notification_references = mocker.patch(
            'app.celery.tasks.get_notification_references',
            return_value=['1', '2', '3']
        )
    with freeze_time('2017-01-01 17:30'):
        yield SendApiMocks


def test_should_set_up_local_directory_structure(mocks, mocker):
    localdir = mocker.patch('app.celery.tasks.LocalDir')

    send_api_notifications_to_dvla('')

    localdir.assert_called_once_with('api')


def test_should_get_api_file_from_s3(mocks):
    filename = '2017-01-01T12:34:56Z-dvla-notifications.txt'

    send_api_notifications_to_dvla(filename)

    mocks.get_api_from_s3.assert_called_once_with(filename)


def test_should_send_api_file(mocks):
    send_api_notifications_to_dvla('2017-01-01T12:34:56Z-dvla-notifications.txt')

    mocks.send_file.assert_called_once_with(
        local_file='/tmp/dvla-file-storage/api/2017-01-01T12:34:56Z-dvla-notifications.txt',
    )


def test_should_get_references_out_of_api_file(mocks):
    send_api_notifications_to_dvla('my-file')

    mocks.get_notification_references.assert_called_once_with('my-file')


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


def test_should_update_notifications_to_success_in_1k_batches(mocker, mocks):
    mocker.patch(
        'app.celery.tasks.get_notification_references',
        return_value=list(range(10000))
    )
    send_api_notifications_to_dvla('')

    assert mocks.send_task.call_count == 10
    assert mocks.send_task.mock_calls[0][2]['args'] == (list(range(1000)),)
    assert mocks.send_task.mock_calls[1][2]['args'] == (list(range(1000, 2000)),)
    assert mocks.send_task.mock_calls[2][2]['args'] == (list(range(2000, 3000)),)

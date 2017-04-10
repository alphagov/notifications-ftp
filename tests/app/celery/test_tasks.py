from app.celery.tasks import send_files_to_dvla
import app
from unittest.mock import call
from freezegun import freeze_time
import pytest


def test_should_call_get_file_for_each_job_id(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):
        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', return_value="DVLA-FILE")
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file')
        mocker.patch('app.notify_celery.send_task')

        send_files_to_dvla(["1", "2", "3"])

        app.celery.tasks.ensure_local_file_directory.assert_called_once_with()
        assert app.celery.tasks.get_file_from_s3.call_args_list == [
            call("test-dvla-file-per-job", "1"),
            call("test-dvla-file-per-job", "2"),
            call("test-dvla-file-per-job", "3")
        ]
        app.celery.tasks.concat_files.assert_called_once_with()
        app.celery.tasks.ftp_client.send_file.assert_called_once_with("/tmp/dvla-file-storage/DVLA-FILE")
        assert app.notify_celery.send_task.call_args_list == [
            call(name="update-letter-job-to-sent", args=("1",), queue="notify"),
            call(name="update-letter-job-to-sent", args=("2",), queue="notify"),
            call(name="update-letter-job-to-sent", args=("3",), queue="notify")
        ]
        app.celery.tasks.remove_local_file_directory.assert_called_once_with()


def test_should_call_remove_local_files_in_event_of_exception(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):
        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', return_value="DVLA-FILE")
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file', side_effect=Exception("FAILED TO SEND FILE"))
        mocker.patch('app.notify_celery.send_task')

        with pytest.raises(Exception) as excinfo:
            send_files_to_dvla(["1"])
            app.celery.tasks.ftp_client.send_file.assert_called_once_with("/tmp/dvla-file-storage/DVLA-FILE")
            assert 'FAILED TO SEND FILE' in str(excinfo.value)
            app.notify_celery.send_task.assert_not_called()
            app.celery.tasks.remove_local_file_directory.assert_called_once_with()

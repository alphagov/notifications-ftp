from app.celery.tasks import send_files_to_dvla
import app
from unittest.mock import call
from freezegun import freeze_time
import pytest


def test_should_set_up_local_directory_structure(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):

        def side_effect():
            return "DVLA-FILE", ["1", "2", "3"], []

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file')
        mocker.patch('app.notify_celery.send_task')

        send_files_to_dvla(["1", "2", "3"])
        app.celery.tasks.ensure_local_file_directory.assert_called_once_with()


def test_should_call_fetch_from_s3_for_each_job(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):

        def side_effect():
            return "DVLA-FILE", ["1", "2", "3"], []

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
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


def test_should_call_concat_files(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):

        def side_effect():
            return "DVLA-FILE", ["1", "2", "3"], []

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file')
        mocker.patch('app.notify_celery.send_task')

        send_files_to_dvla(["1", "2", "3"])
        app.celery.tasks.concat_files.assert_called_once_with()


def test_should_call_send_ftp_with_dvla_file(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):

        def side_effect():
            return "DVLA-FILE", ["1", "2", "3"], []

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file')
        mocker.patch('app.notify_celery.send_task')

        send_files_to_dvla(["1", "2", "3"])
        app.celery.tasks.ftp_client.send_file.assert_called_once_with("/tmp/dvla-file-storage/DVLA-FILE")


def test_should_call_remove_local_files_on_success(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):
        def side_effect():
            return "DVLA-FILE", ["1", "2", "3"], []

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file')
        mocker.patch('app.notify_celery.send_task')

        send_files_to_dvla(["1", "2", "3"])
        app.celery.tasks.remove_local_file_directory.assert_called_once_with()


def test_should_call_remove_local_files_in_event_of_exception(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):
        def side_effect():
            return "DVLA-FILE", ["1", "2", "3"], []

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file', side_effect=Exception("FAILED TO SEND FILE"))
        mocker.patch('app.notify_celery.send_task')

        with pytest.raises(Exception) as excinfo:
            send_files_to_dvla(["1"])
            app.celery.tasks.ftp_client.send_file.assert_called_once_with("/tmp/dvla-file-storage/DVLA-FILE")
            assert 'FAILED TO SEND FILE' in str(excinfo.value)
            app.notify_celery.send_task.assert_not_called()
            app.celery.tasks.remove_local_file_directory.assert_called_once_with()


def test_should_update_success_tasks_with_succesfully_processed_files(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):
        def side_effect():
            return "DVLA-FILE", ["1", "2", "3"], []

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
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


def test_should_update_failed_tasks_with_unsuccesfully_processed_files(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):
        def side_effect():
            return "DVLA-FILE", ["2"], ["1", "3"]

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3')
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file')
        mocker.patch('app.notify_celery.send_task')

        send_files_to_dvla(["1", "2", "3"])

        assert app.notify_celery.send_task.call_args_list == [
            call(name="update-letter-job-to-sent", args=("2",), queue="notify"),
            call(name="update-letter-job-to-error", args=("1",), queue="notify"),
            call(name="update-letter-job-to-error", args=("3",), queue="notify")
        ]


def test_should_update_failed_tasks_with_unsuccesfully_processed_files_and_failed_s3_downloads(client, mocker):
    with freeze_time('2016-01-01T17:00:00'):
        def side_effect():
            return "DVLA-FILE", ["2"], ["3"]

        def failed_to_download(*args, **kwargs):
            if args[1] == '1':
                return False
            return True

        mocker.patch('app.celery.tasks.ensure_local_file_directory')
        mocker.patch('app.celery.tasks.get_file_from_s3', side_effect=failed_to_download)
        mocker.patch('app.celery.tasks.concat_files', side_effect=side_effect)
        mocker.patch('app.celery.tasks.remove_local_file_directory')
        mocker.patch('app.celery.tasks.ftp_client.send_file')
        mocker.patch('app.notify_celery.send_task')

        send_files_to_dvla(["1", "2", "3"])

        assert app.notify_celery.send_task.call_args_list == [
            call(name="update-letter-job-to-sent", args=("2",), queue="notify"),
            call(name="update-letter-job-to-error", args=("1",), queue="notify"),
            call(name="update-letter-job-to-error", args=("3",), queue="notify")
        ]

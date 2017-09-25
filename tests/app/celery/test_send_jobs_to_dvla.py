from unittest.mock import call, Mock

from botocore.exceptions import ClientError as S3Error
import pytest

import app
from app.celery.tasks import send_jobs_to_dvla
from app.sftp.ftp_client import FtpException


@pytest.fixture
def mocks(mocker, client):
    class SendJobMocks:
        get_job_from_s3 = mocker.patch('app.celery.tasks.get_job_from_s3')
        concat_files = mocker.patch('app.celery.tasks.concat_files', return_value='DVLA-FILE')
        send_file = mocker.patch('app.celery.tasks.ftp_client.send_file')
        send_task = mocker.patch('app.notify_celery.send_task')
    yield SendJobMocks


def test_should_set_up_local_directory_structure(mocks, mocker):
    localdir = mocker.patch('app.celery.tasks.LocalDir')

    send_jobs_to_dvla(["1", "2", "3"])

    localdir.assert_called_once_with('job')


def test_should_call_fetch_from_s3_for_each_job(mocks):
    send_jobs_to_dvla(["1", "2", "3"])

    assert mocks.get_job_from_s3.call_args_list == [
        call("1"),
        call("2"),
        call("3")
    ]


def test_should_call_concat_files(mocks, mocker):
    return_vals = [Mock(), Mock(), Mock()]
    mocks.get_job_from_s3.side_effect = return_vals

    send_jobs_to_dvla(["1", "2", "3"])

    mocks.concat_files.assert_called_once_with(return_vals)


def test_should_call_send_ftp_with_dvla_file(mocks):
    send_jobs_to_dvla(["1", "2", "3"])

    mocks.send_file.assert_called_once_with("/tmp/dvla-file-storage/job/DVLA-FILE")


def test_should_update_success_tasks_with_succesfully_processed_files(mocks):
    send_jobs_to_dvla(["1", "2", "3"])

    assert mocks.send_task.call_args_list == [
        call(
            name="update-letter-job-to-sent",
            args=("1",),
            queue="notify-internal-tasks"
        ),
        call(
            name="update-letter-job-to-sent",
            args=("2",),
            queue="notify-internal-tasks"
        ),
        call(
            name="update-letter-job-to-sent",
            args=("3",),
            queue="notify-internal-tasks"
        )
    ]


def test_should_update_failed_tasks_if_s3_error(mocks):
    mocks.get_job_from_s3.side_effect = S3Error)

    send_jobs_to_dvla(["1", "2", "3"])

    assert not mocks.send_file.called
    assert mocks.send_task.call_args_list == [
        call(
            name="update-letter-job-to-error",
            args=("1",),
            queue="notify-internal-tasks"
        ),
        call(
            name="update-letter-job-to-error",
            args=("2",),
            queue="notify-internal-tasks"
        ),
        call(
            name="update-letter-job-to-error",
            args=("3",),
            queue="notify-internal-tasks"
        )
    ]


def test_should_update_failed_tasks_if_ftp_error(mocks):
    mocks.send_file.side_effect = FtpException

    send_jobs_to_dvla(["1", "2", "3"])

    assert mocks.send_task.call_args_list == [
        call(
            name="update-letter-job-to-error",
            args=("1",),
            queue="notify-internal-tasks"
        ),
        call(
            name="update-letter-job-to-error",
            args=("2",),
            queue="notify-internal-tasks"
        ),
        call(
            name="update-letter-job-to-error",
            args=("3",),
            queue="notify-internal-tasks"
        )
    ]

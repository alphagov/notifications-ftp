from pathlib import Path
import os
from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from app.files.file_utils import (
    get_dvla_file_name,
    get_new_dvla_filename,
    job_file_name_for_job,
    get_job_from_s3,
    get_api_from_s3,
    _get_file_from_s3,
    concat_files,
    get_notification_references,
    LocalDir
)


FOO_SUBFOLDER = '/tmp/dvla-file-storage/foo'


@pytest.fixture
def local_job_dir(client):
    with LocalDir('job') as job_folder:
        yield job_folder


@pytest.fixture
def local_api_dir(client):
    with LocalDir('api') as api_folder:
        yield api_folder


def test_get_file_from_s3_should_return_filename_on_successful_s3_download(local_job_dir, mocker):
    s3_mock = Mock()
    mocker.patch('app.files.file_utils.boto3.client', return_value=s3_mock)

    ret = _get_file_from_s3('bucket', 'job', 'foo.txt')

    assert ret == 'foo.txt'
    assert s3_mock.download_fileobj.call_args[0][0] == 'bucket'
    assert s3_mock.download_fileobj.call_args[0][1] == 'foo.txt'
    # 3rd arg is location to download to
    assert s3_mock.download_fileobj.call_args[0][2].name == '/tmp/dvla-file-storage/job/foo.txt'


def test_get_job_from_s3_should_get_correct_file_to_download(local_job_dir, mocker):
    mocked = mocker.patch('app.files.file_utils._get_file_from_s3')

    get_job_from_s3('1234')

    mocked.assert_called_once_with(
        'test-dvla-file-per-job',
        'job',
        '1234-dvla-job.text'
    )


def test_get_api_from_s3_should_get_correct_file_to_download(local_api_dir, mocker):
    mocked = mocker.patch('app.files.file_utils._get_file_from_s3')

    get_api_from_s3('2017-01-01T12:34:56Z.txt')

    mocked.assert_called_once_with(
        'test-dvla-letter-api-files',
        'api',
        '2017-01-01T12:34:56Z.txt'
    )


def test_get_dvla_file_name():
    with freeze_time('2016-01-01T17:00:00'):
        assert get_dvla_file_name() == 'Notify-201601011700-rq.txt'


def test_get_new_dvla_file_name():
    # increment from 17:59 to 18:00
    assert get_new_dvla_filename('Notify-201601011759-rq.txt') == 'Notify-201601011800-rq.txt'


def test_should_make_job_filename_from_job_id():
    assert job_file_name_for_job('3872ce4a-8817-44b9-bca6-972ac6706b59') == '3872ce4a-8817-44b9-bca6-972ac6706b59-dvla-job.text'  # noqa


def test_concat_files_only_concats_provided_files(local_job_dir):
    subfolder = Path(local_job_dir)
    files = ['file-1', 'file-2', 'file-3']

    for filename in files:
        with (subfolder / filename).open('w') as test_file:
            test_file.write(filename + "\n")

    with freeze_time('2016-01-01T17:00:00'):
        dvla_filename = concat_files(['file-1', 'file-2'])

    assert dvla_filename == "Notify-201601011700-rq.txt"

    with (subfolder / dvla_filename).open() as concat_file:
        assert concat_file.read() == 'file-1\nfile-2\n'


def test_local_dir_creates_directory_if_not_present_and_then_removes_at_end(client):
    assert not os.path.exists(FOO_SUBFOLDER)
    with LocalDir('foo') as foo:
        assert os.path.exists(FOO_SUBFOLDER)
    assert not os.path.exists(FOO_SUBFOLDER)


def test_local_dir_keeps_directory_if_present_but_still_removes_at_end(client):
    os.makedirs(FOO_SUBFOLDER)
    with LocalDir('foo') as foo:
        assert os.path.exists(FOO_SUBFOLDER)
    assert not os.path.exists(FOO_SUBFOLDER)


def test_local_dir_removes_even_if_files_present(client):
    with LocalDir('foo') as foo:
        with (foo / 'a.txt').open('w') as test_file:
            test_file.write('test\n')
        assert len(os.listdir(FOO_SUBFOLDER)) == 1
    assert not os.path.exists(FOO_SUBFOLDER)


def test_get_notification_references_gets_references_from_file(local_api_dir):
    dvla_file_contents = '\n'.join([
        '140|001|001||ABC0000000000000|||||||||||||1||2|3|4|5|6|WC2B 6NH|||||||||hello',
        '140|001|001||DEF0000000000000|||||||||||||1||2|3|4|5|6|WC2B 6NH|||||||||hello',
        '140|001|001||GHI0000000000000|||||||||||||1||2|3|4|5|6|WC2B 6NH|||||||||hello',
        ''
    ])
    filename = (local_api_dir / 'foo.txt')
    with filename.open('w') as test_file:
        test_file.write(dvla_file_contents)

    refs = get_notification_references(filename)

    assert refs == ['ABC0000000000000', 'DEF0000000000000', 'GHI0000000000000']

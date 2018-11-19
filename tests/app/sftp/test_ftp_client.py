from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from app.sftp.ftp_client import upload_file, upload_zip, FtpException, check_file_exist_and_is_right_size


@pytest.fixture
def mocks(client):
    class SendZipMocks:
        mock_bad_lstat = Mock(st_size=10)
        mock_lstat = Mock(st_size=1)
        mock_remote_file = Mock(write=Mock(), __exit__=Mock(), __enter__=Mock())
        mock_data = b'\x00'
        mock_remote_filename = 'NOTIFY.20160101170000.ZIP'
    yield SendZipMocks


@freeze_time('2016-01-01T17:00:00')
@pytest.mark.parametrize('local_file,remote_filename', [
    ('/tmp/something/foo.txt', 'Notify-201601011700-rq.txt')
])
def test_send_file_generates_remote_filename(local_file, remote_filename):
    sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[remote_filename])
    )

    upload_file(sftp, local_file, Mock())

    sftp.chdir.assert_called_once_with('notify')
    sftp.put.assert_called_once_with(local_file, remotepath='~/notify/' + remote_filename)


@freeze_time('2016-01-01T17:00:00')
@pytest.mark.parametrize('local_file,remote_filename', [
    ('/tmp/something/foo.txt', 'Notify-201601011701-rq.txt')
])
def test_send_file_increments_filename_if_exists(local_file, remote_filename):
    sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=True),
        listdir=Mock(return_value=[remote_filename])
    )

    upload_file(sftp, local_file, Mock())

    sftp.put.assert_called_once_with(local_file, remotepath='~/notify/' + remote_filename)


@freeze_time('2016-01-01T17:00:00')
def test_send_file_errors_if_file_wasnt_put_on():
    local_file = '/tmp/something/foo.txt'
    sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[])
    )

    with pytest.raises(FtpException):
        upload_file(sftp, local_file, Mock())


@freeze_time('2016-01-01T17:00:00')
def test_send_zip_generates_remote_filename(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[mocks.mock_remote_filename]),
        open=Mock(return_value=mocks.mock_remote_file),
        lstat=Mock(return_value=mocks.mock_lstat),
    )

    upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename, Mock())

    mock_zip_sftp.chdir.assert_called_once_with('notify')
    mock_zip_sftp.open.assert_called_once_with('~/notify/' + mocks.mock_remote_filename, mode='xw')


@freeze_time('2016-01-01T17:00:00')
def test_send_zip_increments_filename_if_exists(mocks):
    mock_new_remote_filename = 'NOTIFY.20160101170100.ZIP'

    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=True),
        listdir=Mock(return_value=[mock_new_remote_filename]),
        open=Mock(return_value=mocks.mock_remote_file),
        lstat=Mock(return_value=mocks.mock_lstat),
    )

    upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename, Mock())

    mock_zip_sftp.open.assert_called_once_with('~/notify/' + mock_new_remote_filename, mode='xw')


@freeze_time('2016-01-01T17:00:00')
def test_send_zip_errors_if_file_wasnt_put_on(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[]),
        open=Mock(return_value=mocks.mock_remote_file),
    )

    with pytest.raises(FtpException):
        upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename, Mock())


@freeze_time('2016-01-01T17:00:00')
def test_send_zip_errors_if_remote_file_size_is_different(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[mocks.mock_remote_filename]),
        open=Mock(return_value=mocks.mock_remote_file),
        lstat=Mock(return_value=mocks.mock_bad_lstat),
    )

    with pytest.raises(FtpException):
        upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename, Mock())


def test_file_exists_with_correct_size(mocks):
    zip_data = b'some data'
    remote_filename = "a-file-that-worked-but-still-threw-exception.zip"
    mock_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[remote_filename]),
        lstat=Mock(return_value=Mock(st_size=len(zip_data))),
    )

    check_file_exist_and_is_right_size(mock_sftp, remote_filename, len(zip_data))
    mock_sftp.lstat.assert_called_once_with('~/notify/{}'.format(remote_filename))


def test_file_exists_with_correct_size_throws_exception_when_file_does_not_exist(mocks):
    zip_data = b'some data'
    remote_filename = "file_does_not_exist_remotely.zip"
    mock_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=["any-file-but-the-right-one"]),
    )

    with pytest.raises(expected_exception=FtpException) as e:
        check_file_exist_and_is_right_size(mock_sftp, remote_filename, len(zip_data))
        assert e.value == "Zip file {} not uploaded".format(remote_filename)
    mock_sftp.listdir.assert_called_once_with()


def test_file_exists_with_correct_size_throws_exception_file_exists_with_wrong_size(mocks):
    zip_data = b'some data'
    remote_filename = "file_does_not_exist_remotely.zip"
    mock_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[remote_filename]),
        lstat=Mock(st_size=1)
    )

    with pytest.raises(expected_exception=FtpException) as e:
        check_file_exist_and_is_right_size(mock_sftp, remote_filename, len(zip_data))
        assert e.value == "Zip file {} uploaded but size is incorrect: is {}, expected {}d".format(
            remote_filename, len(zip_data), 1)
    mock_sftp.lstat.assert_called_once_with('~/notify/{}'.format(remote_filename))

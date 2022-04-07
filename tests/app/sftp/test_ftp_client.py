from unittest.mock import Mock

import pytest

from app.sftp.ftp_client import (
    FtpException,
    check_file_exist_and_is_right_size,
    upload_zip,
)


@pytest.fixture
def mocks(client):
    class SendZipMocks:
        mock_bad_lstat = Mock(st_size=10)
        mock_lstat = Mock(st_size=1)
        mock_remote_file = Mock(write=Mock(), __exit__=Mock(return_value=False), __enter__=Mock())
        mock_data = b'\x00'
        mock_remote_filename = 'NOTIFY.20160101170000.ZIP'
    yield SendZipMocks


def test_upload_zip_success(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[mocks.mock_remote_filename]),
        open=Mock(return_value=mocks.mock_remote_file),
        lstat=Mock(return_value=mocks.mock_lstat),
    )

    upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename)

    mock_zip_sftp.chdir.assert_called_once_with('notify')
    mock_zip_sftp.open.assert_called_once_with('~/notify/' + mocks.mock_remote_filename, mode='w')
    mocks.mock_remote_file.__enter__.return_value.set_pipelined.assert_called_once()
    mocks.mock_remote_file.__enter__.return_value.write.assert_called_once()


def test_send_zip_doesnt_overwrite_if_file_exists_with_same_size(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=True),
        listdir=Mock(return_value=[mocks.mock_remote_filename]),
        open=Mock(return_value=mocks.mock_remote_file),
        lstat=Mock(return_value=mocks.mock_lstat),
    )

    upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename)

    assert mock_zip_sftp.open.called is False


def test_send_zip_overwrites_if_file_exists_with_different_size(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=True),
        listdir=Mock(return_value=[mocks.mock_remote_filename]),
        open=Mock(return_value=mocks.mock_remote_file),
        # first time it's called, there's the old file, then we overwrite and put in the new file instead
        lstat=Mock(side_effect=[mocks.mock_bad_lstat, mocks.mock_lstat]),
    )

    upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename)

    mock_zip_sftp.open.assert_called_once_with('~/notify/' + mocks.mock_remote_filename, mode='w')


def test_send_zip_errors_if_file_wasnt_put_on(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[]),
        open=Mock(return_value=mocks.mock_remote_file),
    )

    with pytest.raises(FtpException):
        upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename)


def test_send_zip_errors_if_remote_file_size_is_different(mocks):
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[mocks.mock_remote_filename]),
        open=Mock(return_value=mocks.mock_remote_file),
        lstat=Mock(return_value=mocks.mock_bad_lstat),
    )

    with pytest.raises(FtpException):
        upload_zip(mock_zip_sftp, mocks.mock_data, mocks.mock_remote_filename)


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

    assert str(e.value) == "Zip file file_does_not_exist_remotely.zip not uploaded"
    mock_sftp.listdir.assert_called_once_with()


def test_file_exists_with_correct_size_throws_exception_file_exists_with_wrong_size(mocks):
    zip_data = b'some data'
    remote_filename = "file_does_not_exist_remotely.zip"
    mock_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[remote_filename]),
        lstat=Mock(return_value=Mock(st_size=1))
    )

    with pytest.raises(expected_exception=FtpException) as e:
        check_file_exist_and_is_right_size(mock_sftp, remote_filename, len(zip_data))

    assert str(e.value) == (
        "Zip file file_does_not_exist_remotely.zip uploaded but size is incorrect: "
        "is 1, expected 9"
    )
    mock_sftp.lstat.assert_called_once_with('~/notify/file_does_not_exist_remotely.zip')

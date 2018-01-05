from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from app.sftp.ftp_client import upload_file, upload_zip, FtpException


mock_remote_file = Mock(
    write=Mock(),
    __exit__=Mock(),
    __enter__=Mock()
)

mock_data = b'\x00'
mock_remote_filename = 'NOTIFY.20160101170000.ZIP'


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
def test_send_zip_generates_remote_filename():
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[mock_remote_filename]),
        open=Mock(return_value=mock_remote_file)
    )

    upload_zip(mock_zip_sftp, mock_data, mock_remote_filename, Mock())

    mock_zip_sftp.chdir.assert_called_once_with('notify')
    mock_zip_sftp.open.assert_called_once_with('~/notify/' + mock_remote_filename, mode='xw')


@freeze_time('2016-01-01T17:00:00')
def test_send_zip_increments_filename_if_exists():
    mock_new_remote_filename = 'NOTIFY.20160101170100.ZIP'

    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=True),
        listdir=Mock(return_value=[mock_new_remote_filename]),
        open=Mock(return_value=mock_remote_file)
    )

    upload_zip(mock_zip_sftp, mock_data, mock_remote_filename, Mock())

    mock_zip_sftp.open.assert_called_once_with('~/notify/' + mock_new_remote_filename, mode='xw')


@freeze_time('2016-01-01T17:00:00')
def test_send_zip_errors_if_file_wasnt_put_on():
    mock_zip_sftp = Mock(
        pwd='~/notify',
        exists=Mock(return_value=False),
        listdir=Mock(return_value=[]),
        open=Mock(return_value=mock_remote_file)
    )

    with pytest.raises(FtpException):
        upload_zip(mock_zip_sftp, mock_data, mock_remote_filename, Mock())

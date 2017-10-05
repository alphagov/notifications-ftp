from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from app.sftp.ftp_client import upload_file, FtpException


@freeze_time('2016-01-01T17:00:00')
@pytest.mark.parametrize('local_file,remote_filename', [
    ('/tmp/something/foo.txt', 'Notify-201601011700-rq.txt'),
    ('/tmp/something/foo.zip', 'Notify.201601011700.zip')
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
    ('/tmp/something/foo.txt', 'Notify-201601011701-rq.txt'),
    ('/tmp/something/foo.zip', 'Notify.201601011701.zip')
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

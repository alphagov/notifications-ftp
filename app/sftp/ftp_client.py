from contextlib import contextmanager

import pysftp
from flask import current_app
from monotonic import monotonic

NOTIFY_SUBFOLDER = 'notify'


class FtpException(Exception):
    pass


class FtpClient():
    def init_app(self, app, statsd_client):
        self.host = app.config.get('FTP_HOST')
        self.username = app.config.get('FTP_USERNAME')
        self.password = app.config.get('FTP_PASSWORD')
        self.statsd_client = statsd_client

    @contextmanager
    def _sftp(self):
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            current_app.logger.info("opening connection to {}".format(self.host))
            with pysftp.Connection(self.host, username=self.username, password=self.password, cnopts=cnopts) as sftp:
                yield sftp
        except Exception as e:
            # reraise all exceptions as FtpException to ensure we can handle them down the line
            current_app.logger.exception(e)
            raise FtpException("Failed to sFTP file")

    def send_zip(self, zip_data, filename):
        with self._sftp() as sftp:
            upload_zip(sftp, zip_data, filename, self.statsd_client)

    def file_exists_with_correct_size(self, filename, zip_data_len):
        with self._sftp() as sftp:
            check_file_exist_and_is_right_size(sftp, filename, zip_data_len)


def upload_zip(sftp, zip_data, filename, statsd_client):
    sftp.chdir(NOTIFY_SUBFOLDER)
    zip_data_len = len(zip_data)

    current_app.logger.info("uploading zip {} of total size {:,}".format(filename, zip_data_len))

    start_time = monotonic()

    if sftp.exists('{}/{}'.format(sftp.pwd, filename)):
        stats = sftp.lstat('{}/{}'.format(sftp.pwd, filename))
        if stats.st_size == zip_data_len:
            current_app.logger.info('{} already exists on DVLA ftp with matching filesize {}, skipping'.format(
                filename, stats.st_size
            ))
            return
        else:
            current_app.logger.info('{} already exists on DVLA ftp with different filesize {}, overwriting'.format(
                filename, stats.st_size
            ))

    with sftp.open('{}/{}'.format(sftp.pwd, filename), mode='w') as remote_file:
        remote_file.set_pipelined()
        zip_data = memoryview(zip_data.encode())
        remote_file.write(zip_data)

    statsd_client.timing("ftp-client.zip-upload-time", monotonic() - start_time)

    check_file_exist_and_is_right_size(sftp, filename, zip_data_len)
    current_app.logger.info("Data {} uploaded to DVLA".format(filename))


def check_file_exist_and_is_right_size(sftp, filename, zip_data_len):
    if filename in sftp.listdir():
        stats = sftp.lstat('{}/{}'.format(sftp.pwd, filename))
        if stats.st_size != zip_data_len:
            raise FtpException(
                "Zip file {} uploaded but size is incorrect: is {}, expected {}".format(
                    filename, stats.st_size, zip_data_len))
    else:
        raise FtpException("Zip file {} not uploaded".format(filename))

import os

import pysftp
from flask import current_app
from monotonic import monotonic

from app.files.file_utils import get_dvla_file_name, get_new_dvla_filename

NOTIFY_SUBFOLDER = 'notify'


class FtpException(Exception):
    pass


class FtpClient():
    def init_app(self, app, statsd_client):
        self.host = app.config.get('FTP_HOST')
        self.username = app.config.get('FTP_USERNAME')
        self.password = app.config.get('FTP_PASSWORD')
        self.statsd_client = statsd_client

    def send_file(self, local_file):
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            current_app.logger.info("opening connection to {}".format(self.host))
            with pysftp.Connection(self.host, username=self.username, password=self.password, cnopts=cnopts) as sftp:
                upload_file(sftp, local_file, self.statsd_client)
        except Exception as e:
            # reraise all exceptions as FtpException to ensure we can handle them down the line
            current_app.logger.exception(e)
            raise FtpException("Failed to sFTP file")


def upload_file(sftp, local_file, statsd_client):
    filename_without_path = os.path.split(local_file)[1]
    sftp.chdir(NOTIFY_SUBFOLDER)
    current_app.logger.info("uploading {}".format(local_file))

    start_time = monotonic()

    remote_filename = get_dvla_file_name()

    if sftp.exists('{}/{}'.format(sftp.pwd, remote_filename)):
        # increment the time in the filename by one minute - if there's ALSO a file with that name, then
        # lets just give up as something's definitely gone weird.
        remote_filename = get_new_dvla_filename(remote_filename)
        current_app.logger.warning('{} already exists on DVLA ftp, renaming to {}'.format(
            filename_without_path,
            remote_filename
        ))

    sftp.put(local_file, remotepath='{}/{}'.format(sftp.pwd, remote_filename))

    statsd_client.timing("ftp-client.upload-time", monotonic() - start_time)

    # would be good to check filesize here to be safe - see sftp.listdir_attr
    if remote_filename in sftp.listdir():
        current_app.logger.info("Local file {} uploaded to DVLA as {}".format(local_file, remote_filename))
    else:
        raise FtpException("File {} not uploaded".format(local_file))

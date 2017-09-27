import os

import pysftp
from flask import current_app
from monotonic import monotonic

from app.files.file_utils import get_new_dvla_filename


class FtpException(Exception):
    pass


class FtpClient():
    def init_app(self, app, statsd_client):
        self.host = app.config.get('FTP_HOST')
        self.username = app.config.get('FTP_USERNAME')
        self.password = app.config.get('FTP_PASSWORD')
        self.statsd_client = statsd_client

    def send_file(self, local_filename, remote_filename):
        filename_without_path = os.path.split(filename)[1]
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            current_app.logger.info("opening connection to {}".format(self.host))
            with pysftp.Connection(self.host, username=self.username, password=self.password, cnopts=cnopts) as sftp:
                sftp.chdir('notify')
                current_app.logger.info("uploading {}".format(filename))

                start_time = monotonic()
                if sftp.exists('{}/{}'.format(sftp.pwd, filename_without_path)):
                    # increment the time in the filename by one minute - if there's ALSO a file with that name, then
                    # lets just give up as something's definitely gone weird.
                    remote_filename = get_new_dvla_filename(filename_without_path)
                    current_app.logger.warning('{} already exists on DVLA ftp, renaming to {}'.format(
                        filename_without_path,
                        remote_filename
                    ))
                else:
                    remote_filename = filename_without_path

                sftp.put(filename, remotepath='{}/{}'.format(sftp.pwd, remote_filename))

                self.statsd_client.timing("ftp-client.upload-time", monotonic() - start_time)

                if filename_without_path in sftp.listdir():
                    current_app.logger.info("File {} successfully uploaded".format(filename_without_path))
                else:
                    raise FtpException("File {} not uploaded".format(filename_without_path))
        except Exception as e:
            current_app.logger.exception(e)
            raise FtpException("Failed to sFTP file")

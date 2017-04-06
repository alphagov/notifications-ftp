import pysftp
from flask import current_app
import os
from monotonic import monotonic


class FtpClient():
    def init_app(self, app, statsd_client):
        self.host = app.config.get('FTP_HOST')
        self.username = app.config.get('FTP_USERNAME')
        self.password = app.config.get('FTP_PASSWORD')
        self.statsd_client = statsd_client


    def send_file(self, filename):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        current_app.logger.info("opening connection to {}".format(self.host))
        with pysftp.Connection(self.host, username=self.username, password=self.password, cnopts=cnopts) as sftp:
            sftp.chdir('notify')
            current_app.logger.info("uploading {}".format(filename))

            start_time = monotonic()
            sftp.put(filename)
            self.statsd_client.timing("ftp-client.upload-time", monotonic() - start_time)

            filename_without_path = os.path.split(filename)[1]
            if filename_without_path in sftp.listdir():
                current_app.logger.info("File {} successfully uploaded".format(filename_without_path))
            else:
                current_app.debug(remote_files)
                raise Exception("File {} not uploaded".format(filename_without_path))

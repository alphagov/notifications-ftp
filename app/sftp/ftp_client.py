import pysftp
from flask import current_app


class FtpClient():
    def init_app(self, app):
        self.host = app.config.get('FTP_HOST')
        self.username = app.config.get('FTP_USERNAME')
        self.password = app.config.get('FTP_PASSWORD')

    def send_file(self, filename):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(self.host, username=self.username, password=self.password, cnopts=cnopts) as sftp:
            sftp.chdir('notify')
            sftp.put(filename)

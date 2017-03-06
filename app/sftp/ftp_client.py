import pysftp
from flask import current_app

class FtpClient():
    def init_app(self, app):
        self.host = app.config.get('FTP_HOST')
        self.username = app.config.get('FTP_USERNAME')
        self.password = app.config.get('FTP_PASSWORD')

    def send_file(self, filename):
        with pysftp.Connection(self.host, username=self.username, password=self.password) as sftp:
            sftp.put(filename)

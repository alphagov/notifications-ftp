import os

import StringIO
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler, FileProducer
from pyftpdlib.servers import FTPServer

from notifications_python_client.notifications import NotificationsAPIClient


service_id = "ID"
secret = "SECRET"

client = NotificationsAPIClient(
    "http://localhost:6011",
    service_id,
    secret
)



class NotifyStringIO(StringIO.StringIO):
    name = "NotifyStringIO"


class NotifyFileProducer(FileProducer):
    """Producer wrapper for file[-like] objects."""

    buffer_size = 65536

    def __init__(self, file_like_object, type='i'):
        """Initialize the producer with a data_wrapper appropriate to TYPE.
         - (file) file: the file[-like] object.
         - (str) type: the current TYPE, 'a' (ASCII) or 'i' (binary).
        """
        self.file_like_object = file_like_object

    def more(self):
        """Attempt a chunk of data of size self.buffer_size."""
        return self.file_like_object.read()


class NotifyFTPHandler(FTPHandler):

    def ftp_RETR(self, file):

        content = client.get_all_notifications()

        file_like_object = NotifyStringIO(content)

        producer = NotifyFileProducer(file_like_object)

        self.push_dtp_data(producer, isproducer=True, file=file_like_object, cmd="RETR")
        return file


def main():
    # Instantiate a dummy authorizer for managing 'virtual' users
    authorizer = DummyAuthorizer()

    # Define a new user having full r/w permissions and a read-only
    # anonymous user
    authorizer.add_user('__USER__', '__PASSWORD__', '.', perm='elradfmwM')
    authorizer.add_anonymous(os.getcwd())

    # Instantiate FTP handler class
    handler = NotifyFTPHandler
    handler.authorizer = authorizer

    # Define a customized banner (string returned when client connects)
    handler.banner = "pyftpdlib based ftpd ready."

    # Specify a masquerade address and the range of ports to use for
    # passive connections.  Decomment in case you're behind a NAT.
    #handler.masquerade_address = '151.25.42.11'
    #handler.passive_ports = range(60000, 65535)

    # Instantiate FTP server class and listen on 0.0.0.0:2121
    address = ('', 2121)
    server = FTPServer(address, handler)

    # set a limit for connections
    server.max_cons = 256
    server.max_cons_per_ip = 10

    # start ftp server
    server.serve_forever()

if __name__ == '__main__':
    main()
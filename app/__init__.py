import os

from app.celery.celery import NotifyCelery
from app.sftp.ftp_client import FtpClient

from notifications_utils import logging
from notifications_utils.clients.statsd.statsd_client import StatsdClient
notify_celery = NotifyCelery()
statsd_client = StatsdClient()
ftp_client = FtpClient()


def create_app(application):
    from app.config import configs

    notify_environment = os.environ['NOTIFY_ENVIRONMENT']

    application.config.from_object(configs[notify_environment])

    notify_celery.init_app(application)
    statsd_client.init_app(application)
    logging.init_app(application, statsd_client)
    ftp_client.init_app(application, statsd_client)

    return application

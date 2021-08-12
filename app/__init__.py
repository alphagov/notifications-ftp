import os

from notifications_utils import logging
from notifications_utils.clients.statsd.statsd_client import StatsdClient

from app.celery.celery import NotifyCelery
from app.sftp.ftp_client import FtpClient

notify_celery = NotifyCelery()
statsd_client = StatsdClient()
ftp_client = FtpClient()


def create_app(application):
    from app.config import configs

    notify_environment = os.environ['NOTIFY_ENVIRONMENT']

    application.config.from_object(configs[notify_environment])

    statsd_client.init_app(application)
    logging.init_app(application, statsd_client)
    notify_celery.init_app(application)
    ftp_client.init_app(application)

    return application

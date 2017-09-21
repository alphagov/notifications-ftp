import os

from kombu import Exchange, Queue


class Config(object):
    # Hosted graphite statsd prefix
    STATSD_PREFIX = os.getenv('STATSD_PREFIX')

    NOTIFICATION_QUEUE_PREFIX = os.getenv('NOTIFICATION_QUEUE_PREFIX')

    FTP_HOST = os.getenv('FTP_HOST')
    FTP_USERNAME = os.getenv('FTP_USERNAME')
    FTP_PASSWORD = os.getenv('FTP_PASSWORD')

    # Logging
    DEBUG = False
    LOGGING_STDOUT_JSON = os.getenv('LOGGING_STDOUT_JSON') == '1'

    ###########################
    # Default config values ###
    ###########################

    NOTIFY_APP_NAME = 'api'
    NOTIFY_ENVIRONMENT = 'development'
    AWS_REGION = 'eu-west-1'
    NOTIFY_LOG_PATH = '/var/log/notify/application.log'

    BROKER_URL = 'sqs://'
    BROKER_TRANSPORT_OPTIONS = {
        'region': AWS_REGION,
        'polling_interval': 1,
        'visibility_timeout': 310,
        'queue_name_prefix': NOTIFICATION_QUEUE_PREFIX
    }
    CELERY_ENABLE_UTC = True
    CELERY_TIMEZONE = 'Europe/London'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_IMPORTS = ('app.celery.tasks', )
    CELERY_QUEUES = [
        Queue('process-ftp-tasks', Exchange('default'), routing_key='process-ftp-tasks')
    ]

    STATSD_ENABLED = False
    STATSD_HOST = "statsd.hostedgraphite.com"
    STATSD_PORT = 8125

    LOCAL_FILE_STORAGE_PATH = "~/dvla-file-storage"

    DVLA_JOB_BUCKET_NAME = None
    DVLA_API_BUCKET_NAME = None

######################
# Config overrides ###
######################


class Development(Config):
    NOTIFY_ENVIRONMENT = 'development'
    NOTIFICATION_QUEUE_PREFIX = 'development'
    DEBUG = True
    LOCAL_FILE_STORAGE_PATH = "/tmp/dvla-file-storage"

    DVLA_JOB_BUCKET_NAME = 'development-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'development-dvla-letter-api-files'

class Test(Config):
    NOTIFY_ENVIRONMENT = 'test'
    DEBUG = True
    STATSD_ENABLED = True
    STATSD_HOST = "localhost"
    STATSD_PORT = 1000
    LOCAL_FILE_STORAGE_PATH = "/tmp/dvla-file-storage"

    DVLA_JOB_BUCKET_NAME = 'test-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'test-dvla-letter-api-files'


class Preview(Config):
    NOTIFY_ENVIRONMENT = 'preview'

    DVLA_JOB_BUCKET_NAME = 'preview-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'preview-dvla-letter-api-files'


class Staging(Config):
    NOTIFY_ENVIRONMENT = 'staging'
    STATSD_ENABLED = True

    DVLA_JOB_BUCKET_NAME = 'staging-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'staging-dvla-letter-api-files'


class Production(Config):
    NOTIFY_ENVIRONMENT = 'production'
    STATSD_ENABLED = True

    DVLA_JOB_BUCKET_NAME = 'production-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'production-dvla-letter-api-files'


configs = {
    'development': Development,
    'test': Test,
    'preview': Preview,
    'staging': Staging,
    'production': Production,
}

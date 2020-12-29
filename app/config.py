import os

from kombu import Exchange, Queue


class Config(object):
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
    AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')
    NOTIFY_LOG_PATH = os.getenv('NOTIFY_LOG_PATH', '/var/log/notify/application.log')

    CELERY = {
        'accept_content': ['json'],
        'broker_url': 'sqs://',
        'broker_transport_options': {
            'region': AWS_REGION,
            'polling_interval': 1,
            'visibility_timeout': 310,
            'queue_name_prefix': NOTIFICATION_QUEUE_PREFIX,
        },
        'enable_utc': True,
        'timezone': 'Europe/London',
        'imports': ['app.celery.tasks'],
        'task_queues': [
            Queue('process-ftp-tasks', Exchange('default'), routing_key='process-ftp-tasks')
        ],
        'task_serializer': 'json',
        # restart workers after each task is executed - this will help prevent any memory leaks (not that we should be
        # encouraging sloppy memory management). Since we only run a handful of tasks per day, and none are time
        # sensitive, the extra couple of seconds overhead isn't seen to be a huge issue.
        'worker_max_tasks_per_child': 1
    }

    STATSD_ENABLED = False
    STATSD_HOST = "statsd.hostedgraphite.com"
    STATSD_PORT = 8125

    LOCAL_FILE_STORAGE_PATH = "~/dvla-file-storage"

    DVLA_JOB_BUCKET_NAME = None
    DVLA_API_BUCKET_NAME = None

    LETTERS_PDF_BUCKET_NAME = None

######################
# Config overrides ###
######################


class Development(Config):
    DEBUG = True
    NOTIFICATION_QUEUE_PREFIX = 'development'
    NOTIFY_LOG_PATH = 'application.log'
    LOCAL_FILE_STORAGE_PATH = "/tmp/dvla-file-storage"

    DVLA_JOB_BUCKET_NAME = 'development-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'development-dvla-letter-api-files'

    LETTERS_PDF_BUCKET_NAME = 'development-letters-pdf'


class Test(Development):
    STATSD_ENABLED = False
    LOCAL_FILE_STORAGE_PATH = "/tmp/dvla-file-storage"

    DVLA_JOB_BUCKET_NAME = 'test-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'test-dvla-letter-api-files'

    LETTERS_PDF_BUCKET_NAME = 'test-letters-pdf'


class Preview(Config):

    DVLA_JOB_BUCKET_NAME = 'preview-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'preview-dvla-letter-api-files'

    LETTERS_PDF_BUCKET_NAME = 'preview-letters-pdf'


class Staging(Config):
    STATSD_ENABLED = False

    DVLA_JOB_BUCKET_NAME = 'staging-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'staging-dvla-letter-api-files'

    LETTERS_PDF_BUCKET_NAME = 'staging-letters-pdf'


class Production(Config):
    STATSD_ENABLED = False

    DVLA_JOB_BUCKET_NAME = 'production-dvla-file-per-job'
    DVLA_API_BUCKET_NAME = 'production-dvla-letter-api-files'

    LETTERS_PDF_BUCKET_NAME = 'production-letters-pdf'


configs = {
    'development': Development,
    'test': Test,
    'preview': Preview,
    'staging': Staging,
    'live': Production,
    'production': Production,
}

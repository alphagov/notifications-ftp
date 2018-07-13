#!/usr/bin/env python
from flask import Flask

from app import notify_celery, create_app  # noqa: notify_celery required to get celery running
from credstash import getAllSecrets
import os

os.environ['AWS_REGION'] = 'eu-west-1'
os.environ.update(getAllSecrets(region="eu-west-1"))

application = Flask('delivery')
create_app(application)
application.app_context().push()

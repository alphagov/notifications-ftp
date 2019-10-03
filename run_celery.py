#!/usr/bin/env python
from flask import Flask

from app import notify_celery, create_app  # noqa: notify_celery required to get celery running

application = Flask('notify-ftp')
create_app(application)
application.app_context().push()

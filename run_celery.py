#!/usr/bin/env python

from app.performance import init_performance_monitoring

init_performance_monitoring()

from flask import Flask  # noqa

from app import notify_celery, create_app  # noqa: notify_celery required to get celery running

application = Flask('notify-ftp')
create_app(application)
application.app_context().push()

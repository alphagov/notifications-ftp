#!/usr/bin/env python
from app import notify_celery, create_app  # noqa: notify_celery required to get celery running
from credstash import getAllSecrets
import os

os.environ.update(getAllSecrets(region="eu-west-1"))

application = create_app()
application.app_context().push()

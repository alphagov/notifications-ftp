from app import notify_celery
from flask import current_app


@notify_celery.task(name="test")
def test():
    current_app.logger.info("running task")

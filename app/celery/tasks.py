from app import notify_celery
from flask import current_app
from boto3 import resource


@notify_celery.task(name="test")
def test():
    current_app.logger.info("running task")


@notify_celery.task(name="send-files-to-dvla")
def send_files_to_dvla(bucket_name, jobs_ids):
    current_app.logger.info("running task")
    current_app.logger.info("Bucket name {}".format(bucket_name))
    current_app.logger.info("Jobs {}".format(tuple(jobs_ids)))

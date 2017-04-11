from app import notify_celery, ftp_client
from flask import current_app
from boto3 import resource
from app.files.file_utils import (
    get_file_from_s3,
    job_id_from_filename,
    remove_local_file_directory,
    concat_files,
    ensure_local_file_directory
)
from app.statsd_decorators import statsd


@notify_celery.task(name="test")
def test():
    current_app.logger.info("running task")


@notify_celery.task(name="send-files-to-dvla")
@statsd(namespace="tasks")
def send_files_to_dvla(jobs_ids):
    try:
        ensure_local_file_directory()
        for job_id in jobs_ids:
            get_file_from_s3(current_app.config['DVLA_UPLOAD_BUCKET_NAME'], job_id)

        dvla_file, success, failure = concat_files()
        ftp_client.send_file("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], dvla_file))

        for success_files in success:
            notify_celery.send_task(
                name="update-letter-job-to-sent", args=(job_id_from_filename(success_files),), queue="notify"
            )
        for failed_files in failure:
            notify_celery.send_task(
                name="update-letter-job-to-error", args=(job_id_from_filename(failed_files),), queue="notify"
            )
    finally:
        remove_local_file_directory()

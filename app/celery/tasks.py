from app import notify_celery, ftp_client
from flask import current_app
from app.files.file_utils import (
    get_file_from_s3,
    job_id_from_filename,
    remove_local_file_directory,
    concat_files,
    ensure_local_file_directory
)
from app.statsd_decorators import statsd
from app.sftp.ftp_client import FtpException


NOTIFY_QUEUE = 'notify-internal-tasks'


@notify_celery.task(name="send-files-to-dvla")
@statsd(namespace="tasks")
def send_files_to_dvla(jobs_ids):
    send_jobs_to_dvla(jobs_ids)


@notify_celery.task(name="send-jobs-to-dvla")
@statsd(namespace="tasks")
def send_jobs_to_dvla(jobs_ids):
    try:
        failed_jobs = []
        ensure_local_file_directory()
        for job_id in jobs_ids:
            if not get_file_from_s3(current_app.config['DVLA_UPLOAD_BUCKET_NAME'], job_id):
                failed_jobs.append(job_id)

        dvla_file, successful_jobs, failures = concat_files()
        failed_jobs += [job_id_from_filename(failed_file) for failed_file in failures]

        if successful_jobs:
            ftp_client.send_file("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], dvla_file))

        for successful_job in successful_jobs:
            notify_celery.send_task(
                name="update-letter-job-to-sent", args=(job_id_from_filename(successful_job),), queue=NOTIFY_QUEUE
            )
        for failed_job in failed_jobs:
            notify_celery.send_task(
                name="update-letter-job-to-error", args=(failed_job,), queue=NOTIFY_QUEUE
            )
    except FtpException:
        for job_id in jobs_ids:
            notify_celery.send_task(
                name="update-letter-job-to-error", args=(job_id,), queue=NOTIFY_QUEUE
            )
    finally:
        remove_local_file_directory()

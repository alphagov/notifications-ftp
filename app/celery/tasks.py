from flask import current_app

from app import notify_celery, ftp_client
from app.files.file_utils import (
    get_job_from_s3,
    get_api_from_s3,
    concat_files,
    rename_api_file,
    LocalDir,
    get_notification_references
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
def send_jobs_to_dvla(job_ids):
    try:
        with LocalDir('job') as job_folder:
            job_filenames = [get_job_from_s3(job_id) for job_id in job_ids]

            dvla_file = concat_files(job_filenames)

            ftp_client.send_file(str(job_folder / dvla_file))
    except:
        current_app.logger.exception('FTP app failed to send jobs')
        task_name = 'update-letter-job-to-error'
    else:
        task_name = 'update-letter-job-to-sent'
    finally:
        for job_id in job_ids:
            notify_celery.send_task(
                name=task_name, args=(job_id,), queue=NOTIFY_QUEUE
            )

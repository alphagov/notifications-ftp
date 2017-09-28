from flask import current_app

from app import notify_celery, ftp_client
from app.files.file_utils import (
    get_dvla_file_name,
    get_job_from_s3,
    get_api_from_s3,
    concat_files,
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
            current_app.logger.info('Sending {} to dvla as {}'.format(job_filenames, dvla_file))

            ftp_client.send_file(
                local_file=str(job_folder / dvla_file),
                remote_filename=dvla_file
            )
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


@notify_celery.task(name="send-api-notifications-to-dvla")
@statsd(namespace="tasks")
def send_api_notifications_to_dvla(filename):
    # get pipe file from S3
    with LocalDir('api') as api_folder:
        get_api_from_s3(filename)

        notification_references = get_notification_references(filename)
        current_app.logger.info(
            'Sending {} notifications from {} to dvla'.format(
                len(notification_references),
                filename
            )
        )

        try:
            ftp_client.send_file(
                local_file=str(api_folder / filename),
                remote_filename=get_dvla_file_name()
            )
        except FtpException:
            # if there's an s3 error we won't know what notifications to update, so only worry about FTP issues
            current_app.logger.exception('FTP app failed to send api messages')
            task_name = "update-letter-notifications-to-error"
        else:
            task_name = "update-letter-notifications-to-sent"

        update_notifications(task_name, notification_references)


def update_notifications(task_name, references):
    # split up references into 1000 item sublists to ensure we don't go over SQS's max item size of 256kb
    for notification_references in chunk_list(references, 1000):
        notify_celery.send_task(
            name=task_name, args=(notification_references,), queue=NOTIFY_QUEUE
        )


def chunk_list(items, n):
    # third parameter is step
    for i in range(0, len(items), n):
        yield items[i:i + n]

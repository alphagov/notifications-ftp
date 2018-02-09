import json
from flask import current_app

from botocore.exceptions import ClientError
from notifications_utils.s3 import s3upload as utils_s3upload

from app import notify_celery, ftp_client
from app.files.file_utils import (
    get_job_from_s3,
    get_api_from_s3,
    get_zip_of_letter_pdfs_from_s3,
    concat_files,
    LocalDir,
    get_notification_references,
    get_notification_references_from_s3_filenames,
    get_dvla_file_name,
)
from app.statsd_decorators import statsd
from app.sftp.ftp_client import FtpException

NOTIFY_QUEUE = 'notify-internal-tasks'


@notify_celery.task(name="send-jobs-to-dvla")
@statsd(namespace="tasks")
def send_jobs_to_dvla(job_ids):
    try:
        with LocalDir('job') as job_folder:
            job_filenames = [get_job_from_s3(job_id) for job_id in job_ids]
            dvla_file = concat_files(job_filenames)
            current_app.logger.info('Sending {} to dvla'.format(job_filenames))

            ftp_client.send_file(
                local_file=str(job_folder / dvla_file)
            )
    except Exception:
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
                local_file=str(api_folder / filename)
            )
        except FtpException:
            # if there's an s3 error we won't know what notifications to update, so only worry about FTP issues
            current_app.logger.exception('FTP app failed to send api messages')
            task_name = "update-letter-notifications-to-error"
        else:
            task_name = "update-letter-notifications-to-sent"

        update_notifications(task_name, notification_references)


@notify_celery.task(name="zip-and-send-letter-pdfs")
@statsd(namespace="tasks")
def zip_and_send_letter_pdfs(filenames_to_zip):
    folder_date = filenames_to_zip[0].split('/')[0]

    current_app.logger.info(
        "Starting to zip {file_count} letter PDFs in memory from {folder}".format(
            file_count=len(filenames_to_zip),
            folder=folder_date
        )
    )

    try:
        zip_data = get_zip_of_letter_pdfs_from_s3(filenames_to_zip)
        zip_file_name = get_dvla_file_name(file_ext='.zip')

        # upload a record to s3 of each zip file we send to DVLA - this is just a list of letter filenames so we can
        # match up their references with DVLA
        utils_s3upload(
            filedata=json.dumps(filenames_to_zip).encode(),
            region=current_app.config['AWS_REGION'],
            bucket_name=current_app.config['LETTERS_PDF_BUCKET_NAME'],
            file_location='{}/zips_sent/{}.TXT'.format(folder_date, zip_file_name)
        )
        ftp_client.send_zip(zip_data, zip_file_name)
    except ClientError:
        current_app.logger.exception('FTP app failed to download PDF from S3 bucket {}'.format(folder_date))
        task_name = "update-letter-notifications-to-error"
    except FtpException:
        current_app.logger.exception('FTP app failed to send api messages')
        task_name = "update-letter-notifications-to-error"
    else:
        task_name = "update-letter-notifications-to-sent"

    refs = get_notification_references_from_s3_filenames(filenames_to_zip)
    update_notifications(task_name, refs)


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

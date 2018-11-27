import json
from flask import current_app

from botocore.exceptions import ClientError
from notifications_utils.s3 import s3upload as utils_s3upload

from app import notify_celery, ftp_client
from app.files.file_utils import (
    get_zip_of_letter_pdfs_from_s3,
    get_notification_references_from_s3_filenames,
    get_dvla_file_name,
)
from app.statsd_decorators import statsd
from app.sftp.ftp_client import FtpException

NOTIFY_QUEUE = 'notify-internal-tasks'


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
        try:
            # check if file exists with the right size.
            # It has happened that an IOError occurs but the files are present on the remote server.
            ftp_client.file_exists_with_correct_size(zip_file_name, len(zip_data))
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

import concurrent.futures

import boto3
from botocore.exceptions import ClientError
from flask import current_app

from app.files.in_memory_zip import InMemoryZip


def get_zip_of_letter_pdfs_from_s3(filenames):
    bucket_name = current_app.config['LETTERS_PDF_BUCKET_NAME']
    imz = InMemoryZip()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_files_from_s3 = {
            executor.submit(_get_file_from_s3_in_memory, bucket_name, filename): filename for filename in filenames
        }
        for completed_file in concurrent.futures.as_completed(future_files_from_s3):
            filename = future_files_from_s3[completed_file]
            pdf_filename = filename.split('/')[-1]
            imz.append(pdf_filename, completed_file.result())

    return imz.read()


def get_notification_references_from_s3_filenames(filenames):
    # assumes S3 filename is like: 2017-12-06/NOTIFY.ABCDEFG1234567890.SOME.SUFFIX.PDF
    return [f.split('.')[1] for f in filenames]


def _get_file_from_s3_in_memory(bucket_name, filename):
    s3 = boto3.resource('s3')
    obj = s3.Object(
        bucket_name=bucket_name,
        key=filename
    )
    return obj.get()["Body"].read()


def file_exists_on_s3(bucket_name, filename):
    s3 = boto3.resource('s3')
    try:
        s3.Object(bucket_name, filename).get()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return False
        else:
            current_app.logger.exception('Error checking to see if {}/{} exists'.format(bucket_name, filename))
            raise
    return True

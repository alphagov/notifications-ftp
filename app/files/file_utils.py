from datetime import datetime

from flask import current_app
import boto3

from app.files.in_memory_zip import InMemoryZip

DVLA_FILENAME_FORMAT = 'Notify-%Y%m%d%H%M-rq.txt'
DVLA_ZIP_FILENAME_FORMAT = 'NOTIFY.%Y%m%d%H%M%S.ZIP'


def get_dvla_file_name(dt=None, file_ext='.txt'):
    dt = dt or datetime.utcnow()
    return dt.strftime(_get_dvla_format(file_ext))


def get_zip_of_letter_pdfs_from_s3(filenames):
    bucket_name = current_app.config['LETTERS_PDF_BUCKET_NAME']
    imz = InMemoryZip()

    for i, filename in enumerate(filenames):
        pdf_filename = filename.split('/')[-1]
        pdf_file = _get_file_from_s3_in_memory(bucket_name, filename)
        imz.append(pdf_filename, pdf_file)

    return imz.read()


def get_notification_references_from_s3_filenames(filenames):
    # assumes S3 filename is like: 2017-12-06/NOTIFY.ABCDEFG1234567890.D.2.C.C.20171206184702.PDF
    return [f.split('.')[1] for f in filenames]


def _get_file_from_s3_in_memory(bucket_name, filename):
    s3 = boto3.resource('s3')
    obj = s3.Object(
        bucket_name=bucket_name,
        key=filename
    )
    return obj.get()["Body"].read()


def _get_dvla_format(file_ext='.txt'):
    if file_ext and file_ext.lower() == '.zip':
        dvla_format = DVLA_ZIP_FILENAME_FORMAT
    else:
        dvla_format = DVLA_FILENAME_FORMAT
    return dvla_format

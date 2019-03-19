from flask import current_app
import boto3

from app.files.in_memory_zip import InMemoryZip


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

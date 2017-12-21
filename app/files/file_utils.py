import os
from pathlib import Path
from datetime import datetime, timedelta
from shutil import (
    copyfileobj,
    rmtree
)

from flask import current_app
import boto3

from app.files.in_memory_zip import InMemoryZip

DVLA_FILENAME_FORMAT = 'Notify-%Y%m%d%H%M-rq.txt'
DVLA_ZIP_FILENAME_FORMAT = 'Notify.%Y%m%d%H%M.zip'


def _get_dvla_format(file_ext='.txt'):
    if file_ext and file_ext.lower() == '.zip':
        dvla_format = DVLA_ZIP_FILENAME_FORMAT
    else:
        dvla_format = DVLA_FILENAME_FORMAT
    return dvla_format


def get_dvla_file_name(dt=None, file_ext='.txt'):
    dt = dt or datetime.utcnow()
    return dt.strftime(_get_dvla_format(file_ext))


def get_new_dvla_filename(old_filename):
    file_ext = os.path.splitext(old_filename)[1]
    # increment the time by one minute
    old_datetime = datetime.strptime(old_filename, _get_dvla_format(file_ext))

    return get_dvla_file_name(dt=old_datetime + timedelta(minutes=1), file_ext=file_ext)


def job_file_name_for_job(job_id):
    return "{}-dvla-job.text".format(job_id)


def get_job_from_s3(job_id):
    bucket_name = current_app.config['DVLA_JOB_BUCKET_NAME']
    filename = job_file_name_for_job(job_id)

    return _get_file_from_s3(bucket_name, 'job', filename)


def get_api_from_s3(filename):
    bucket_name = current_app.config['DVLA_API_BUCKET_NAME']
    return _get_file_from_s3(bucket_name, 'api', filename)


def get_zip_of_letter_pdfs_from_s3(filenames):
    bucket_name = current_app.config['LETTERS_PDF_BUCKET_NAME']
    imz = InMemoryZip()

    for filename in filenames:
        pdf_filename = filename.split('/')[-1]
        pdf_file = _get_file_from_s3_in_memory(bucket_name, filename)
        imz.append(pdf_filename, pdf_file)

    return imz.read()


def _get_file_from_s3_in_memory(bucket_name, filename):
    s3 = boto3.resource('s3')
    obj = s3.Object(
        bucket_name=bucket_name,
        key=filename
    )
    return obj.get()["Body"].read()


def _get_file_from_s3(bucket_name, subfolder, filename):
    s3 = boto3.client('s3')
    output_filename = full_path_to_file(subfolder, filename)
    with open(output_filename, 'wb+') as out_file:
        s3.download_fileobj(bucket_name, filename, out_file)
    return filename


def full_path_to_file(subfolder, filename):
    return str(Path(current_app.config['LOCAL_FILE_STORAGE_PATH']) / subfolder / filename)


def concat_files(filenames):
    dvla_file_name = get_dvla_file_name()
    full_path_to_dvla_file = full_path_to_file('job', dvla_file_name)

    with open(full_path_to_dvla_file, 'w+', encoding="utf-8") as dvla_file:
        current_app.logger.info("making {}".format(dvla_file.name))
        for job_file in filenames:
            job_file_path = full_path_to_file('job', job_file)
            with open(job_file_path, 'r', encoding="utf-8") as readfile:
                current_app.logger.info("concatenating {}".format(job_file))
                copyfileobj(readfile, dvla_file)
    return dvla_file_name


def _create_local_file_directory(subfolder):
    folder = '{}/{}'.format(current_app.config['LOCAL_FILE_STORAGE_PATH'], subfolder)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def _remove_local_file_directory(subfolder):
    folder = '{}/{}'.format(current_app.config['LOCAL_FILE_STORAGE_PATH'], subfolder)
    if os.path.exists(folder):
        rmtree(folder, ignore_errors=False)


def get_notification_references(filename):
    with (Path(current_app.config['LOCAL_FILE_STORAGE_PATH']) / 'api' / filename).open('r', encoding='utf-8') as dvla_file:  # noqa
        return [line.split('|')[4] for line in dvla_file.readlines() if line]


class LocalDir:
    def __init__(self, subfolder):
        self.subfolder = subfolder

    def __enter__(self):
        new_folder = _create_local_file_directory(self.subfolder)
        return Path(new_folder)

    def __exit__(self, *args):
        _remove_local_file_directory(self.subfolder)

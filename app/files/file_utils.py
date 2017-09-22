import os
from pathlib import Path
from datetime import datetime
from shutil import (
    copyfileobj,
    rmtree
)

from flask import current_app
import boto3


def get_dvla_file_name():
    return "Notify-{}-rq.txt".format(datetime.utcnow().strftime("%Y%m%d%H%M"))


def job_file_name_for_job(job_id):
    return "{}-dvla-job.text".format(job_id)


def get_job_from_s3(job_id):
    bucket_name = current_app.config['DVLA_JOB_BUCKET_NAME']
    filename = job_file_name_for_job(job_id)

    return _get_file_from_s3(bucket_name, 'job', filename)


def get_api_from_s3(filename):
    bucket_name = current_app.config['DVLA_API_BUCKET_NAME']
    return _get_file_from_s3(bucket_name, 'api', filename)


def _get_file_from_s3(bucket_name, subfolder, filename):
    s3 = boto3.client('s3')
    output_filename = full_path_to_file(subfolder, filename)
    with open(output_filename, 'wb+') as out_file:
        s3.download_fileobj(bucket_name, filename, out_file)
    return output_filename


def full_path_to_file(subfolder, filename):
    return "{}/{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], subfolder, filename)


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


def rename_api_file(filename):
    current = Path(current_app.config['LOCAL_FILE_STORAGE_PATH']) / 'api' / filename
    new = current.parent / get_dvla_file_name()
    current.rename(new)
    return new


def get_notification_references(filename):
    with Path(filename).open('r') as dvla_file:
        return [line.split('|')[4] for line in dvla_file.readlines() if line]


class LocalDir:
    def __init__(self, subfolder):
        self.subfolder = subfolder

    def __enter__(self):
        new_folder = _create_local_file_directory(self.subfolder)
        return Path(new_folder)

    def __exit__(self, *args):
        _remove_local_file_directory(self.subfolder)

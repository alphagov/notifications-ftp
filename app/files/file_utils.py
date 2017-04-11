import os
from flask import current_app
from datetime import datetime
from shutil import (
    copyfileobj,
    rmtree
)
import boto3


def dvla_file_name_for_concatanted_file():
    return "Notify-{}-rq.txt".format(datetime.utcnow().strftime("%Y%m%d%H%M"))


def job_file_name_for_job(job_id):
    return "{}-dvla-job.text".format(job_id)


def job_id_from_filename(job_filename):
    return job_filename.split("-")[0]


def get_file_from_s3(bucket_name, job_id):
    s3 = boto3.client('s3')
    filename = job_file_name_for_job(job_id)
    with open("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], filename), 'wb') as job_file:
        s3.download_fileobj(bucket_name, filename, job_file)


def concat_files():
    dvla_filename = dvla_file_name_for_concatanted_file()
    all_files = os.listdir(current_app.config['LOCAL_FILE_STORAGE_PATH'])

    success = []
    failure = []

    if len(all_files) > 0:
        with open(
                "{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], dvla_filename), 'w+', encoding="utf-8"
        ) as dvla_file:
            current_app.logger.info("making {}".format(dvla_file.name))
            for job_file in all_files:
                try:
                    with open(
                            "{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], job_file),
                            'r',
                            encoding="utf-8"
                    ) as readfile:
                        current_app.logger.info("concatenating {}".format(job_file))
                        copyfileobj(readfile, dvla_file)
                        success.append(job_file)
                except Exception as e:
                    current_app.logger.debug("Failed to concat {}".format(job_file))
                    current_app.logger.exception(e)
    return dvla_filename, success, failure


def ensure_local_file_directory():
    if not os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH']):
        create_local_file_directory()


def create_local_file_directory():
    if not os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH']):
        os.makedirs(current_app.config['LOCAL_FILE_STORAGE_PATH'])


def remove_local_file_directory():
    if os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH']):
        rmtree(current_app.config['LOCAL_FILE_STORAGE_PATH'], ignore_errors=False)

import os
from flask import current_app
from datetime import datetime
import shutil


def dvla_file_name_for_concatanted_file():
    return "Notify-{}-rq.txt".format(datetime.utcnow().strftime("%Y%m%d%H%M"))


def job_file_name_for_job(job_id):
    return "{}-dvla-job.text".format(job_id)


def get_file_from_s3():
    pass


def concat_files():
    dvla_filename = dvla_file_name_for_concatanted_file()
    all_files = os.listdir(current_app.config['LOCAL_FILE_STORAGE_PATH'])

    if len(all_files) > 0:
        with open("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], dvla_filename), 'w+') as dvla_file:
            for job_file in all_files:
                with open("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], job_file), 'r') as readfile:
                    shutil.copyfileobj(readfile, dvla_file)


def ensure_local_file_directory():
    return os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH'])


def create_local_file_directory():
    return os.makedirs(current_app.config['LOCAL_FILE_STORAGE_PATH'])

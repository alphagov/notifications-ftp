import os
from flask import current_app
from freezegun import freeze_time

from app.files.file_utils import (
    create_local_file_directory,
    ensure_local_file_directory,
    concat_files,
    job_file_name_for_job,
    dvla_file_name_for_concatanted_file
)


def test_dvla_file_name_for_concatanted_file():
    with freeze_time('2016-01-01T17:00:00'):
        assert dvla_file_name_for_concatanted_file() == "Notify-201601011700-rq.txt"


def test_should_make_job_filename_from_job_id():
    assert job_file_name_for_job("1234") == "1234-dvla-job.text"


def test_should_create_directory_for_dval_files(client):
    assert not ensure_local_file_directory()
    create_local_file_directory()
    assert ensure_local_file_directory()


def test_should_create_single_file_from_all_files_in_directory(client):
    with freeze_time('2016-01-01T17:00:00'):
        files = ['file-1', 'file-2', 'file-3']
        create_local_file_directory()
        for file in files:
            with open("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], file), 'w+') as test_file:
                test_file.write(file + "\n")

        concat_files()

        with open(
                "{}/Notify-201601011700-rq.txt".format(current_app.config['LOCAL_FILE_STORAGE_PATH'])
        ) as concat_file:
            lines = concat_file.readlines()
            assert lines[0].rstrip() == 'file-1'
            assert lines[1].rstrip() == 'file-2'
            assert lines[2].rstrip() == 'file-3'


def test_should_leave_an_empty_directory_if_no_files_in_directory(client):
    with freeze_time('2016-01-01T17:00:00'):
        create_local_file_directory()
        concat_files()
        assert len(os.listdir(current_app.config['LOCAL_FILE_STORAGE_PATH'])) == 0

import os
from flask import current_app
from freezegun import freeze_time

from app.files.file_utils import (
    create_local_file_directory,
    ensure_local_file_directory,
    concat_files,
    job_file_name_for_job,
    dvla_file_name_for_concatanted_file,
    remove_local_file_directory
)


def test_dvla_file_name_for_concatanted_file():
    with freeze_time('2016-01-01T17:00:00'):
        assert dvla_file_name_for_concatanted_file() == "Notify-201601011700-rq.txt"


def test_should_make_job_filename_from_job_id():
    assert job_file_name_for_job("1234") == "1234-dvla-job.text"


def test_should_create_directory_for_dval_files(client):
    assert not os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH'])
    ensure_local_file_directory()
    assert os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH'])


def test_should_delete_all_files(client):
    ensure_local_file_directory()
    files = ['file-1', 'file-2', 'file-3']
    ensure_local_file_directory()
    for file in files:
        with open("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], file), 'w+') as test_file:
            test_file.write(file + "\n")

    assert len(os.listdir(current_app.config['LOCAL_FILE_STORAGE_PATH'])) == 3
    remove_local_file_directory()
    assert not os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH'])


def test_should_delete_all_files_should_handle_case_where_folder_doesnt_exist(client):
    remove_local_file_directory()
    assert not os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH'])


def test_should_delete_all_files_should_handle_case_where_folder_has_no_files(client):
    ensure_local_file_directory()
    remove_local_file_directory()
    assert not os.path.exists(current_app.config['LOCAL_FILE_STORAGE_PATH'])


def test_should_create_single_file_from_all_files_in_directory(client):
    with freeze_time('2016-01-01T17:00:00'):
        files = ['file-1', 'file-2', 'file-3']
        ensure_local_file_directory()
        for file in files:
            with open("{}/{}".format(current_app.config['LOCAL_FILE_STORAGE_PATH'], file), 'w+') as test_file:
                test_file.write(file + "\n")

        filename = concat_files()

        assert filename == "Notify-201601011700-rq.txt"

        with open(
                "{}/Notify-201601011700-rq.txt".format(current_app.config['LOCAL_FILE_STORAGE_PATH'])
        ) as concat_file:
            lines = [line.rstrip() for line in concat_file.readlines()]
            assert len(lines) == 3
            assert 'file-1' in lines
            assert 'file-2' in lines
            assert 'file-3' in lines


def test_should_leave_an_empty_directory_if_no_files_in_directory(client):
    with freeze_time('2016-01-01T17:00:00'):
        ensure_local_file_directory()
        concat_files()
        assert len(os.listdir(current_app.config['LOCAL_FILE_STORAGE_PATH'])) == 0

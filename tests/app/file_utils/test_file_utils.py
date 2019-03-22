from io import BytesIO
from unittest.mock import call
from zipfile import ZipFile

import boto3
from moto import mock_s3
from flask import current_app

from app.files.file_utils import (
    get_zip_of_letter_pdfs_from_s3,
    _get_file_from_s3_in_memory,
    get_notification_references_from_s3_filenames
)


FOO_SUBFOLDER = '/tmp/dvla-file-storage/foo'


def test_get_notification_references_from_s3():
    filenames = [
        '2017-12-06/NOTIFY.ABC0000000000000.D.2.C.C.20171206184702.PDF',
        '2017-12-06/NOTIFY.DEF0000000000000.D.2.C.C.20171206184710.PDF'
    ]
    refs = get_notification_references_from_s3_filenames(filenames)

    assert set(refs) == set(['ABC0000000000000', 'DEF0000000000000'])


def test_get_zip_of_letter_pdfs_from_s3(notify_ftp, mocker):
    mocked = mocker.patch('app.files.file_utils._get_file_from_s3_in_memory', return_value=b'\x00\x01')

    zip_data = get_zip_of_letter_pdfs_from_s3(['2017-01-01/TEST1.PDF', '2017-01-01/TEST2.PDF'])

    bucket_name = current_app.config['LETTERS_PDF_BUCKET_NAME']
    calls = [
        call(bucket_name, '2017-01-01/TEST1.PDF'),
        call(bucket_name, '2017-01-01/TEST2.PDF')
    ]
    mocked.assert_has_calls(calls)

    zipfile = ZipFile(BytesIO(zip_data))

    assert zipfile.namelist()[0] == 'TEST1.PDF'
    assert zipfile.namelist()[1] == 'TEST2.PDF'
    assert zipfile.read('TEST1.PDF') == b'\x00\x01'
    assert zipfile.read('TEST2.PDF') == b'\x00\x01'


@mock_s3
def test_get_file_from_s3_in_memory_should_return_file_contents_on_successful_s3_download():
    bucket_name = 'bucket'
    filename = 'foo.txt'

    # use moto to mock out s3
    conn = boto3.resource('s3', region_name='eu-west-1')
    conn.create_bucket(Bucket=bucket_name)
    s3 = boto3.client('s3', region_name='eu-west-1')
    s3.put_object(Bucket=bucket_name, Key=filename, Body=b'\x00')

    ret = _get_file_from_s3_in_memory(bucket_name, filename)

    assert ret == b'\x00'

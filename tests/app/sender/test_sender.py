import json

from freezegun import freeze_time

import app


def test_should_send_correct_file(client, mocker):
    mocker.patch('app.ftp_client.send_file')

    with freeze_time('2017-01-01 12:00'):
        response = client.post('/send?filename=test.txt')
    json_resp = json.loads(response.get_data(as_text=True))
    app.ftp_client.send_file.assert_called_with(
        local_filename="/tmp/test.txt",
    )
    assert response.status_code == 200
    assert json_resp['filename'] == "test.txt"

import json
import app


def test_should_send_correct_file(client, mocker):
    mocker.patch('app.ftp_client.send_file')

    response = client.post('/send?filename=test.txt')
    json_resp = json.loads(response.get_data(as_text=True))
    app.ftp_client.send_file.assert_called_with("/tmp/test.txt")
    assert response.status_code == 200
    assert json_resp['filename'] == "test.txt"

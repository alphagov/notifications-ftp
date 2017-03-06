import pysftp

### Requires latest pip versions (sudo -H pip3 install --upgrade pip)

with pysftp.Connection('', username='', password='') as sftp:
    sftp.put("/tmp/test.file")

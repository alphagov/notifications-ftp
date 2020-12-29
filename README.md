# notifications-ftp

Celery app that sends letters from GOV.UK Notify to DVLA over FTP

## Setting Up

### AWS credentials

To run the FTP application, you will need appropriate AWS credentials. You should receive these from whoever administrates your AWS account. Make sure you've got both an access key id and a secret access key.

Your aws credentials should be stored in a folder located at `~/.aws`. Follow [Amazon's instructions](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-config-files) for storing them correctly.

### Virtualenv

```
mkvirtualenv -p /usr/local/bin/python3 notifications-ftp
```


##  To run the application

First, run `scripts/bootstrap.sh` to install dependencies. If you're install dependencies manually, you should run
`pip install -r requirements_dev.txt` to install pycurl with openssl.

Create a local environment.sh file containing the following:

```
echo "
export NOTIFICATION_QUEUE_PREFIX="YOUR_OWN_PREFIX"
export NOTIFY_ENVIRONMENT="development"
export FTP_HOST="YOUR_IP_ADDRESS"
export FTP_USERNAME="YOUR_LDAP_USERNAME"
export FTP_PASSWORD="YOUR_LDAP_PASSWORD"
"> environment.sh
```

Then run the Celery app:

```
scripts/run_celery.sh
```

### Troubleshooting

If you see the following error when running the app locally, your pycurl library is not installed correctly. To fix this
uninstall pycurl (`pip uninstall pycurl`), and then run `pip install -r requirements_dev.txt`.

```
[2020-12-29 12:04:55,333: CRITICAL/MainProcess] Unrecoverable error: ImportError('The curl client requires the pycurl library.',)
Traceback (most recent call last):
  File "/Users/leohemsted/.virtualenvs/ftp/lib/python3.6/site-packages/kombu/asynchronous/http/__init__.py", line 20, in get_client
    return hub._current_http_client
AttributeError: 'Hub' object has no attribute '_current_http_client'
[...]
```

##  To test the application

Simply run

```
make test
```

That will run flake8 for code analysis and our unit test suite.

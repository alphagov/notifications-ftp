# notifications-ftp
Notifications FTP Integrations

Application that will handle Notify connecting to FTP based clients.

Basic Flask/Celery python app.


## Setting Up

### AWS credentials

To run the FTP application, you will need appropriate AWS credentials. You should receive these from whoever administrates your AWS account. Make sure you've got both an access key id and a secret access key.

Your aws credentials should be stored in a folder located at `~/.aws`. Follow [Amazon's instructions](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-config-files) for storing them correctly.

### Virtualenv

```
mkvirtualenv -p /usr/local/bin/python3 notifications-ftp
```


##  To run the application

First, run `scripts/bootstrap.sh` to install dependencies.

You need to run the local celery instance. There is a flask app, however this is only used by ELB to keep the instances healthy.

All you need to do is run the celery queue reader.

```
scripts/run_celery.sh
```


##  To test the application

Simply run

```
make build test
```

That will run flake8 for code analysis and our unit test suite.

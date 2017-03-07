# notifications-ftp
Notifications FTP Integrations

Application that will handle Notify connecting to FTP based clients.

Basic Flask/Celery python app.


## Setting Up

### AWS credentials

To run the FTP application, you will need appropriate AWS credentials. You should receive these from whoever administrates your AWS account. Make sure you've got both an access key id and a secret access key.

Your aws credentials should be stored in a folder located at `~/.aws`. Follow [Amazon's instructions](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-config-files) for storing them correctly.

### Virtualenv

```
mkvirtualenv -p /usr/local/bin/python3 notifications-ftp
```


##  To run the application

First, run `scripts/bootstrap.sh` to install dependencies.

You need to run the flask application and a local celery instance.

There are three run scripts for running all the necessary parts.

Flask endpoints
```
scripts/run_app.sh
```

Celery queue reader
```
scripts/run_celery.sh
```

Celery scheduled tasks
```
scripts/run_celery_beat.sh
```


##  To test the application

First, ensure that `scripts/bootstrap.sh` has been run.

Then simply run

```
make test
```

That will run pycodestyle for code analysis and our unit test suite.
=======

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

First, run `scripts/bootstrap.sh` to install dependencies.

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


##  To test the application

Simply run

```
make test
```

That will run flake8 for code analysis and our unit test suite.

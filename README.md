# notifications-ftp

Celery app that sends letters from GOV.UK Notify to DVLA over FTP

## Setting Up

### AWS credentials

To run the API you will need appropriate AWS credentials. See the [Wiki](https://github.com/alphagov/notifications-manuals/wiki/aws-accounts#how-to-set-up-local-development) for more details.

### pycurl

pycurl needs to be installed separately, with some specific compiler flags and steps. You'll need to follow these steps
in any repo where you wish to run celery locally. The following steps have been adapted from https://gist.github.com/vidakDK/de86d751751b355ed3b26d69ecdbdb99


You'll need to run this once per machine you develop on.
```
brew install curl openssl@1.1
# add the new openssl and curl binaries to your path. Note: You may need to change these commands to write to your bashrc or bash_profile if you don't use zsh.
echo 'export PATH="/usr/local/opt/openssl@1.1/bin:$PATH"' >> ~/.zshrc
echo 'export PATH="/usr/local/opt/curl/bin:$PATH"' >> ~/.zshrc

source ~/.zshrc
```

Then run the following command:
```sh
PYCURL_SSL_LIBRARY="openssl" \
LDFLAGS="-L/usr/local/opt/curl/lib" \
CPPFLAGS="-I/usr/local/opt/curl/include" \
pip install --ignore-installed pycurl==7.43.0.6 --global-option="--with-openssl" --global-option="--openssl-dir=/usr/local/opt/openssl@1.1"
```

You can check if the install worked succesfully by running
```sh
python -c "import pycurl; print(pycurl.version)"
```

If the steps worked succesfully, you will see pycurl's version includes "OpenSSL/1.1.1i" or similar (rather than libressl)
```
PycURL/7.43.0.6 libcurl/7.74.0 (SecureTransport) OpenSSL/1.1.1i zlib/1.2.11 brotli/1.0.9 zstd/1.4.8 libidn2/2.3.0 libssh2/1.9.0 nghttp2/1.42.0 librtmp/2.3
```

##  To run the application

First, run `scripts/bootstrap.sh` to install dependencies.

Create a local environment.sh file containing the following:

```sh
echo "
export NOTIFICATION_QUEUE_PREFIX="YOUR_OWN_PREFIX"
export NOTIFY_ENVIRONMENT="development"
export FTP_HOST="YOUR_IP_ADDRESS"
export FTP_USERNAME="YOUR_LDAP_USERNAME"
export FTP_PASSWORD="YOUR_LDAP_PASSWORD"
"> environment.sh
```

Then run the Celery app:

```sh
scripts/run_celery.sh
```

### Troubleshooting

If you see the following error when running the app locally, your pycurl library is not installed correctly. To fix this
follow the steps in the [pycurl section above](#pycurl).

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

```sh
make test
```

That will run flake8 for code analysis and our unit test suite.

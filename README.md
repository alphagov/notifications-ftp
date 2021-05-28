# notifications-ftp

Celery app that sends letters from GOV.UK Notify to DVLA over FTP

## Setting Up

### AWS credentials

To run the API you will need appropriate AWS credentials. See the [Wiki](https://github.com/alphagov/notifications-manuals/wiki/aws-accounts#how-to-set-up-local-development) for more details.

### pycurl

`pycurl` needs to be installed separately, with some specific compiler flags and steps. The following steps have been adapted from https://gist.github.com/vidakDK/de86d751751b355ed3b26d69ecdbdb99

First make sure you have some prerequisite dependencies installed:

```
brew install curl openssl@1.1

# You may need to change these commands to write to your bashrc or bash_profile if you don't use zsh.
echo 'export PATH="/usr/local/opt/openssl@1.1/bin:$PATH"' >> ~/.zshrc
echo 'export PATH="/usr/local/opt/curl/bin:$PATH"' >> ~/.zshrc

source ~/.zshrc
```

Now install `pycurl` manually, with some specific compiler flags and steps.

```sh
PYCURL_SSL_LIBRARY="openssl" \
LDFLAGS="-L/usr/local/opt/curl/lib" \
CPPFLAGS="-I/usr/local/opt/curl/include" \
pip install --ignore-installed pycurl==7.43.0.6 --global-option="--with-openssl" --global-option="--openssl-dir=/usr/local/opt/openssl@1.1"
```

Check if the installation of `pycurl` worked succesfully by running:

```sh
# This should print a string containing "OpenSSL/1.1.1i" (versus "libressl")
python -c "import pycurl; print(pycurl.version)"
```

### `environment.sh`

Create and edit an environment.sh file.

```sh
echo "
export NOTIFICATION_QUEUE_PREFIX="YOUR_OWN_PREFIX"
export NOTIFY_ENVIRONMENT="development"
export FTP_HOST="localhost"
export FTP_USERNAME="YOUR_LDAP_USERNAME" # optional (if running the task)
export FTP_PASSWORD="YOUR_LDAP_PASSWORD" # optional (if running the task)
"> environment.sh
```

Things to change:

- Replace `YOUR_OWN_PREFIX` with `local_dev_<first name>`.
- Replace `YOUR_LDAP_USERNAME` with the one you use to sign in to your machine.
- Replace `YOUR_LDAP_PASSWORD` with the one you use to sign in to your machine.\*

\* _Storing your LDAP password unencrypted is far from ideal. We would like to improve this in the future._

### FTP Server (optional)

This app needs to connect to an FTP server. You can install one locally:

```
brew install pure-ftpd

brew services start pure-ftpd
```

Since the SFTP client does something similar to `ssh localhost`, you also need to enable remote login:

- Go to "System Preferences > Sharing"
- Check the "Remote Login" service

`pure-ftpd` will use your home directory as it's root. The code expects there to be a `notify` directory there, so you will need to create one (or adjust your FTP server settings to use an alternative root directory):

```
mkdir ~/notify
```

##  To run the application

```sh
# install dependencies, etc.
make bootstrap

make run-celery
```

##  To test the application

```sh
# install dependencies, etc.
make bootstrap

make test
```

## To run a local shell

Although this app includes Flask, it's not possible to run `flask shell`. Run the following instead:

```
make shell
```

## To update application dependencies

`requirements.txt` is generated from the `requirements.in` in order to pin versions of all nested dependencies. If `requirements.in` has been changed, run `make freeze-requirements` to regenerate it.

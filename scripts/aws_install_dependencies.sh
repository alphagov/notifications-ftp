#!/bin/bash

set -eo pipefail

echo "Install dependencies"

cd /home/notify-app/notifications-ftp;
# had problems with crypto (required by pysftp) installing cffi, so trying to install it ourselves beforehand
pip3 install cffi>=1.7
pip3 install --find-links=wheelhouse -r /home/notify-app/notifications-ftp/requirements.txt

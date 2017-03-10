#!/bin/bash

set -eo pipefail

echo "Install dependencies"

cd /home/notify-app/notifications-ftp;
pip3 install --find-links=wheelhouse -r /home/notify-app/notifications-ftp/requirements.txt

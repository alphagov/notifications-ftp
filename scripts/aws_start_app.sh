#!/usr/bin/env bash

set -eo pipefail

function start
{
  service=$1
  if [ -e "/etc/systemd/system/${service}.service" ]; then
    echo "Starting ${service}"
    systemctl start "${service}"
  fi
}

start "notifications-ftp"
start "notifications-ftp-celery-worker"

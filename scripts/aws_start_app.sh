#!/usr/bin/env bash

set -eo pipefail

function start
{
  service=$1
  if [ -e "/etc/systemd/system/${service}.service" ]; then
    echo "Starting ${service}"
    systemctl start "${service}"
  elif [ -e "/etc/init/${service}.conf" ]; then
    echo "Starting ${service}"
    service "${service}" start
  fi
}

start "notifications-ftp"
start "notifications-ftp-celery-worker"

#!/usr/bin/env bash

set -eo pipefail

function stop
{
  service=$1
  if [ -e "/etc/systemd/system/${service}.service" ]; then
    echo "stopping ${service}"
    if systemctl stop "${service}"; then
      echo "${service} stopped"
    else
      >&2 echo "Could not stop ${service}"
    fi
  fi
}

stop "notifications-ftp"
stop "notifications-ftp-celery-worker"

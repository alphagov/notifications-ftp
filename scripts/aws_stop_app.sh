#!/usr/bin/env bash

set -eo pipefail

function stop
{
  service=$1
  stop_command="false"
  if [ -e "/etc/systemd/system/${service}.service" ]; then
    stop_command="systemctl stop ${service}"
  elif [ -e "/etc/init/${service}.conf" ]; then
    stop_command="service ${service} stop"
  fi

  echo "stopping ${service}"

  if [ "$($stop_command)" ]; then
    echo "${service} stopped"
  else
    >&2 echo "Could not stop ${service}"
  fi
}

stop "notifications-ftp"
stop "notifications-ftp-celery-worker"

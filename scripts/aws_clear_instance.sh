#!/bin/bash

echo "Removing application and dependencies"

if [ -d "/home/notify-app/notifications-ftp" ]; then
    # Remove and re-create the directory
    rm -rf /home/notify-app/notifications-ftp
    mkdir -p /home/notify-app/notifications-ftp
fi


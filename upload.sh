#!/usr/bin/env bash
# For local development: upload local content to the RPi and restart the service.
# Assumes a host named 'rpi' defined in ~/.ssh/config.

rsync -r \
    --info=progress2 \
    --exclude=.git \
    --filter=':- .gitignore' \
    ./ rpi:~/rpi-enviro-monitor
ssh rpi sudo systemctl restart enviro.service
ssh rpi journalctl -f -o cat -u enviro.service

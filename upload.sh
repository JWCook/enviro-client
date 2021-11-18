#!/usr/bin/env bash
# TODO: Remotely start job via tmux session
rsync -r \
    --info=progress2 \
    --exclude=.git \
    --filter=':- .gitignore' \
    ./ rpi:~/enviro-client
ssh rpi sudo systemctl restart enviro.service
ssh rpi journalctl -f -o cat -u enviro.service

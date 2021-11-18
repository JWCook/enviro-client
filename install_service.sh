#!/usr/bin/env bash
sudo cp enviro.service /etc/systemd/system/
sudo systemctl enable enviro.service
sudo systemctl start  enviro.service
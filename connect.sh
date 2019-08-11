#!/bin/bash

# Connects after updating wpa_supplicant.conf
# https://raspberrypi.stackexchange.com/questions/73749/how-to-connect-to-wifi-without-reboot

sudo systemctl daemon-reload
sudo systemctl restart dhcpcd

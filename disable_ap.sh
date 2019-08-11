#!/bin/bash

# copy over original
sudo cp /etc/default/hostapd config/hostapd
sudo cp /etc/dhcpcd.conf config/dhcpcd.conf
sudo cp /etc/dnsmasq.conf config/dnsmasq.conf

# disable the AP
sudo cp config/hostapd.disabled /etc/default/hostapd
sudo cp config/dhcpcd.conf.disabled /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf.disabled /etc/dnsmasq.conf

systemctl daemon-reload

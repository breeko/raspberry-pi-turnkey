readonly WIFI=ConnectIOT
readonly PASS=Connect
readonly GIT_REPO=https://github.com/breeko/raspberry-pi-turnkey.git

sudo apt-get update
sudo apt-get dist-upgrade -y
sudo apt-get install -y dnsmasq hostapd python3-flask python3-requests git
git clone $GIT_REPO

sudo systemctl stop dnsmasq && sudo systemctl stop hostapd

echo 'interface wlan0 static ip_address=192.168.4.1/24' | sudo tee --append /etc/dhcpcd.conf

sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig  
sudo systemctl daemon-reload
sudo systemctl restart dhcpcd

echo 'interface=wlan0 dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h' | sudo tee --append /etc/dnsmasq.conf

echo 'interface=wlan0
driver=nl80211
ssid='$WIFI'
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase='$PASS'
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP' | sudo tee --append /etc/hostapd/hostapd.conf

echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee --append /etc/default/hostapd

sudo systemctl unmask hostapd.service
sudo systemctl start hostapd && sudo systemctl start dnsmasq

#sudo echo "pi      ALL=(ALL:ALL) ALL" >> /etc/sudoers
echo "pi      ALL=(ALL:ALL) ALL" | sudo tee --append /etc/sudoers

echo "pi -c '/usr/bin/sudo /usr/bin/python3 /home/pi/raspberry-pi-turnkey/startup.py &'" | sudo tee --append /etc/rc.local

sudo raspi-config --expand-rootfs

sudo reboot now
# sudo visudo
# pi      ALL=(ALL:ALL) ALL

# sudo nano /etc/rc.local
# su pi -c '/usr/bin/sudo /usr/bin/python3 /home/pi/raspberry-pi-turnkey/startup.py &'

# SSH over USB
# https://desertbot.io/blog/ssh-into-pi-zero-over-usb

# Share internet over USB
# https://solarianprogrammer.com/2018/12/07/raspberry-pi-zero-internet-usb/
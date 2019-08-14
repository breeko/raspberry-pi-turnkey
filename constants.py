import os

current_path = os.path.dirname(os.path.abspath(__file__))

WPA_CONF_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"
DHCPCD_CONF_PATH = "/etc/dhcpcd.conf"

STARTUP_SCRIPT = "./startup.sh"

IP_REGEX = r"[0-9]{3}\.[0-9]{3}\.[0-9]{1,3}\.[0-9]{1,3}"
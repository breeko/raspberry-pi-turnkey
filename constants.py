import os

current_path = os.path.dirname(os.path.abspath(__file__))

WPA_CONF_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"
TEMP_WPA_CONF_PATH = "{}/config/wpa_supplicant.conf".format(current_path)

DHCPCD_CONF_PATH = "/etc/dhcpcd.conf"
TEMP_DHCPCD_CONF_PATH = "{}/config/dhcpcd.conf".format(current_path)

STARTUP_SCRIPT = "./startup.sh"

# wpa_utils.py
# contains functions for creating and updating wpa_supplicant.conf

import os
import re
import subprocess

from shutil import copyfile
from constants import IP_REGEX

from constants import WPA_CONF_PATH, DHCPCD_CONF_PATH, IP_REGEX

def is_wpa_setup() -> bool:
    """ Returns True if wpa conf file already exists """
    return os.path.isfile(WPA_CONF_PATH)
  
def setup_wpa_conf():
    """ Creates a blank wpa_supplicant file """
    wpa_conf_default = """country=US\nctrl_interface=DIR=/var/run/wpa_supplicant\nupdate_config=1"""
  
    with open(WPA_CONF_PATH, 'w') as f:
        f.write(wpa_conf_default)

def clear_static_ip(path: str) -> None:
  """ Clears any static ip from dhcpcd conf file """
  static_ip_regex = r"""^interface wlan0\n+static ip_address={ip}\/24\n+(static routers={ip})?\n+(static domain_name_servers={ip})?""".format(ip=IP_REGEX)
  with open(path, "r") as f:
    out = f.read()
    updated = re.sub(static_ip_regex, "", out, flags=re.MULTILINE)
  with open(path, "w") as f:
    f.write(updated)

def create_static_ip(path: str, ip: str, router_ip: str) -> None:
  """ Creates a static ip string and inserts it its a dhcpcd conf """
  static_ip = 'interface wlan0\n\nstatic ip_address={}/24\nstatic routers={}\nstatic domain_name_servers={}\n'.format(ip, router_ip, router_ip)
  with open(path, "a+") as f:
    f.write(static_ip)

def set_ip(ip_suffix: str) -> None:
  router_ip = get_router_ip()
  ip_prefix = get_ip_prefix()
  ip = ip_prefix + ip_suffix
  clear_static_ip(path = DHCPCD_CONF_PATH)
  create_static_ip(path = DHCPCD_CONF_PATH, ip = ip, router_ip = router_ip)

def toggle_wlan_services(on: bool) -> None:
    """ Stops wlan0 services """
    if on:
        print(subprocess.check_output(['systemctl', "restart", "dnsmasq", "dhcpcd"]))
        print(subprocess.check_output(['systemctl', "restart", "hostapd"]))
    else:
        # Services need to be stopped to free up wlan0 interface
        print(subprocess.check_output(['systemctl', "stop", "hostapd", "dnsmasq", "dhcpcd"]))


def create_network(ssid: str, password: str) -> str:
    """ Creates the text needed to add a network wpa_supplicant.conf """
    if password == "":
        network = 'network={\n\tssid="' + ssid +'"\n\tkey_mgmt=NONE\n}'
    else:
        network = subprocess.check_output(['wpa_passphrase', ssid, password]).decode("utf-8")

    return network
  
def get_router_ip() -> str:
    """ Returns the ip of the router """
    cmd = "ip r | grep -Po '(?<=default via ){}' | head -1".format(IP_REGEX)
    return subprocess.getoutput(cmd)
  
def get_ip() -> str:
    """ Returns the internal ip of device"""
    cmd = "ifconfig wlan0 | grep -Po '(?<=inet ){}' | head -1".format(IP_REGEX)
    return subprocess.getoutput(cmd)
  
def get_ip_suffix() -> str:
    """ Returns the suffx of the internal ip (e.g. 192.168.1.16 -> 16 """
    ip = get_ip()
    suffix = ip.split(".")[-1]
    return suffix
  
def get_ip_prefix() -> str:
    """ Returns the prefix of the internal ip (e.g. 192.168.1.16 -> 192.168.1. """
    ip = get_ip()
    prefix = ".".join(ip.split(".")[:-1]) + "."
    return prefix
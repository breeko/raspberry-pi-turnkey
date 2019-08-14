#connection_utils.py

# contains functions for checking connection

import time
import subprocess
import os
import signal

from typing import List
from utils import monitor_output, IP_REGEX
from wpa_utils import toggle_wlan_services

def get_ssids(num_attempts: int) -> List[str]:
    """ Returns the available ssids. Since wlan services could be off, tries a number of times before returning an empty list"""
    ssid_list = []
    ssid_out = ""
    for _ in range(num_attempts):
      try:
        ssid_out = subprocess.check_output(('iw', 'dev', 'wlan0', 'scan', 'ap-force'))
        break
      except subprocess.CalledProcessError:
        time.sleep(1)
    ssids = ssid_out.splitlines()
    for s in ssids:
        s = s.strip().decode('utf-8')
        if s.startswith("SSID"):
            a = s.split(": ")
            try:
                ssid_list.append(a[1])
            except:
                pass
    ssid_list = sorted(list(set(ssid_list)))
    return ssid_list

def is_connected(include_shared) -> bool:
  """ Returns True if connected to internet, else False
    args:
      include_shared (bool) -> returns True if connection shared through USB
  """
  google = "www.google.com"
  if not include_shared:
    network = get_connected_network()
    return network != ""
  else:
    try:
      # see if we can resolve the host name -- tells us if there is a DNS listening
      host = socket.gethostbyname(google)
      # connect to the host -- tells us if the host is actually reachable
      s = socket.create_connection((host, 80), 2)
      s.close()
      return True
    except:
      return False

def check_cred(ssid: str, password: str) -> bool:
    """ Validates ssid and password and returns True if valid and False if not valid """
    if len(password) < 8 or len(password) > 63:
        return False
    
    tmpdir = '/tmp/raspberry-pi-turnkey/'
    testconf = os.path.join(tmpdir, 'test.conf')
    wpalog = os.path.join(tmpdir, 'wpa.log')
    wpapid = os.path.join(tmpdir, 'wpa.pid')
    
    if not os.path.exists(tmpdir):
        os.mkdir(tmpdir)
    
    for _file in [testconf, wpalog, wpapid]:
        if os.path.exists(_file):
            os.remove(_file)
    
    # Generate temp wpa.conf
    result = subprocess.check_output(['wpa_passphrase', ssid, password])
    with open(testconf, 'w') as f:
        f.write(result.decode('utf-8'))
    
    toggle_wlan_services(on = False)
    
    result = subprocess.check_output(['wpa_supplicant',
                                        "-Dnl80211",
                                        "-iwlan0",
                                        "-c/" + testconf,
                                        "-f", wpalog,
                                        "-B",
                                        "-P", wpapid])
    
    valid_psk = monitor_output(path=wpalog, success="CTRL-EVENT-CONNECTED", failure="CTRL-EVENT-ASSOC-REJECT", timeout=5)
    
    # Kill wpa_supplicant to stop it from setting up dhcp, dns
    with open(wpapid, 'r') as p:
        pid = p.read()
        pid = int(pid.strip())
        os.kill(pid, signal.SIGTERM)
    
    toggle_wlan_services(on = True) # Restart services
    print("ssid: {} password: {} valid: {}".format(ssid, password, valid_psk))
    return valid_psk
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
  
def get_connected_network() -> str:
    """ Returns the name of the connected network """
    cmd = "iwgetid | grep -Po '(?<=ESSID:\").+(?=\"$)' | head -1"
    return subprocess.getoutput(cmd)
    
def reset_ip() -> None:
    NET_DIR = '/sys/class/net'
  
    subprocess.call(['sudo','systemctl','daemon-reload'])
    subprocess.call(['sudo','systemctl','stop','dhcpcd.service'])
  
    for net_dev in os.listdir(NET_DIR):
      subprocess.call(['sudo','ip','addr','flush','dev',net_dev])
  
    subprocess.call(['sudo','systemctl','start','dhcpcd.service'])
    subprocess.call(['sudo','systemctl','restart','networking.service'])
  
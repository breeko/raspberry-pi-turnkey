import subprocess
from typing import List
import socket
import time
import os
import signal

REMOTE_SERVER = "www.google.com"

def get_ssids() -> List[str]:
    """ Returns the available ssids """
    ssid_list = []
    get_ssid_list = subprocess.check_output(('iw', 'dev', 'wlan0', 'scan', 'ap-force'))
    ssids = get_ssid_list.splitlines()
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

def is_connected() -> bool:
  """ Returns True if connected to internet, else False """
  try:
    # see if we can resolve the host name -- tells us if there is a DNS listening
    host = socket.gethostbyname(REMOTE_SERVER)
    # connect to the host -- tells us if the host is actually reachable
    s = socket.create_connection((host, 80), 2)
    s.close()
    return True
  except:
     pass
  return False

def monitor_output(path:str, success: str, failure: str, timeout: float) -> bool:
  """ Monitors the contents of a file looking for success or failure string.
  Returns True if success found, False if failure found or timeout"""
  start = time.time()
  while True:
    with open(path, "r") as f:
      now = time.time()
      out = f.read()
      if success in out:
        return True
      elif failure in out:
        return False
      elif now - start > timeout:
        return False

def get_current_dir() -> str:
  """ Returns current directory absolute path """
  return os.path.dirname(os.path.abspath(__file__))

def stop_ap(stop: bool) -> None:
  """ Stops wlan0 services """
  if stop:
      # Services need to be stopped to free up wlan0 interface
      print(subprocess.check_output(['systemctl', "stop", "hostapd", "dnsmasq", "dhcpcd"]))
  else:
      print(subprocess.check_output(['systemctl', "restart", "dnsmasq", "dhcpcd"]))
      # time.sleep(2)
      print(subprocess.check_output(['systemctl', "restart", "hostapd"]))

def check_cred(ssid: str, password: str) -> bool:
  '''Validates ssid and password and returns True if valid and False if not valid'''
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

  stop_ap(True)

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

  stop_ap(False) # Restart services
  print("ssid: {} password: {} valid: {}".format(ssid, password, valid_psk))
  return valid_psk

def create_network(ssid: str, password: str) -> str:
  if password == "":
    network = 'network={\n\tssid="' + ssid +'"\n\tkey_mgmt=NONE\n}'
  else:
    network = subprocess.check_output(['wpa_passphrase', ssid, password])
  
  return network

def create_static_ip(ip: str) -> str:
  return 'interface wlan0\n\nstatic ip_address={}/24\nstatic routers=192.168.0.1\nstatic domain_name_servers=192.168.0.1'.format(ip)

def restart_device(disable: bool) -> None:
  if disable:
    subprocess.Popen(["./disable_ap.sh"])
  subprocess.run(["sudo", "restart", "now"])
  
# ip r | grep -Po '(?<=default via )[0-9]{3}.[0-9]{3}.[0-9]{1,3}.[0-9]{1,3}' | head -1
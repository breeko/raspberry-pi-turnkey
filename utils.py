#utils.py

# Contains general functions

import subprocess
import time
import filecmp
from shutil import copyfile

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

def restart_device() -> None:
  """ Restarts the device """
  print("Restarting...")
  subprocess.run(["sudo", "reboot"])

def enable_app() -> None:
  """ Enables the app (sets up network to connect) """
  
  copyfile("config/hostapd", "/etc/default/hostapd")
  copyfile("config/dhcpcd.conf", "/etc/dhcpcd.conf")
  copyfile("config/dnsmasq.conf", "/etc/dnsmasq.conf")

  subprocess.run(["systemctl", "daemon-reload"])

def disable_app() -> None:
  """ Disables the app """

  copyfile("config/hostapd.disabled", "/etc/default/hostapd")
  copyfile("config/dhcpcd.conf.disabled", "/etc/dhcpcd.conf")
  copyfile("config/dnsmasq.conf.disabled", "/etc/dnsmasq.conf")

  subprocess.run(["systemctl", "daemon-reload"])

def is_enabled() -> bool:
  all_same = filecmp.cmp("config/hostapd.disabled", "/etc/default/hostapd") and \
    filecmp.cmp("config/dhcpcd.conf.disabled", "/etc/dhcpcd.conf") and \
    filecmp.cmp("config/dnsmasq.conf.disabled", "/etc/dnsmasq.conf")
  
  return all_same
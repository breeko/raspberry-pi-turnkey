import subprocess
import signal
import re
import json
import time
import os
import socket
import requests
from utils import get_ssids
from config import NAME

from utils import is_connected

from flask import Flask, request, send_from_directory, jsonify, render_template, redirect
app = Flask(__name__, static_url_path='')

currentdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currentdir)

WPA_CONF_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"

STARTUP_SCRIPT = "./startup.sh"

wpa_conf = """country=US
ctrl_interface=DIR=/var/run/wpa_supplicant
update_config=1
network={
    ssid="%s"
    %s
}"""

wpa_conf_default = """country=US
ctrl_interface=DIR=/var/run/wpa_supplicant
update_config=1
"""

@app.route('/')
def main():
    ssids = get_ssids()
    return render_template('index.html', ssids=ssids, message="Configure your {} by providing network information below".format(NAME))

# Captive portal when connected with iOS or Android
@app.route('/generate_204')
def redirect204():
    return redirect("http://192.168.4.1", code=302)

@app.route('/hotspot-detect.html')
def applecaptive():
    return redirect("http://192.168.4.1", code=302)

# Not working for Windows, needs work!
@app.route('/ncsi.txt')
def windowscaptive():
    return redirect("http://192.168.4.1", code=302)

def check_cred(ssid, password):
    '''Validates ssid and password and returns True if valid and False if not valid'''
    wpadir = currentdir + '/wpa/'
    testconf = wpadir + 'test.conf'
    wpalog = wpadir + 'wpa.log'
    wpapid = wpadir + 'wpa.pid'

    if not os.path.exists(wpadir):
        os.mkdir(wpadir)

    for _file in [testconf, wpalog, wpapid]:
        if os.path.exists(_file):
            os.remove(_file)

    # Generate temp wpa.conf
    result = subprocess.check_output(['wpa_passphrase', ssid, password])
    with open(testconf, 'w') as f:
        f.write(result.decode('utf-8'))

    def stop_ap(stop):
        if stop:
            # Services need to be stopped to free up wlan0 interface
            print(subprocess.check_output(['systemctl', "stop", "hostapd", "dnsmasq", "dhcpcd"]))
        else:
            print(subprocess.check_output(['systemctl', "restart", "dnsmasq", "dhcpcd"]))
            time.sleep(15)
            print(subprocess.check_output(['systemctl', "restart", "hostapd"]))

    # Sentences to check for
    fail = "pre-shared key may be incorrect"
    success = "WPA: Key negotiation completed"

    stop_ap(True)

    result = subprocess.check_output(['wpa_supplicant',
                                      "-Dnl80211",
                                      "-iwlan0",
                                      "-c/" + testconf,
                                      "-f", wpalog,
                                      "-B",
                                      "-P", wpapid])

    checkwpa = True
    while checkwpa:
        with open(wpalog, 'r') as f:
            content = f.read()
            if success in content:
                valid_psk = True
                checkwpa = False
            elif fail in content:
                valid_psk = False
                checkwpa = False
            else:
                continue

    # Kill wpa_supplicant to stop it from setting up dhcp, dns
    with open(wpapid, 'r') as p:
        pid = p.read()
        pid = int(pid.strip())
        os.kill(pid, signal.SIGTERM)

    stop_ap(False) # Restart services
    return valid_psk

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/signin', methods=['POST'])
def signin():
    ssid = request.form['ssid']
    password = request.form['password']

    pwd = 'psk="' + password + '"'
    if password == "":
        pwd = "key_mgmt=NONE" # If open AP

    print(ssid, password)
    valid_psk = check_cred(ssid, password)
    if not valid_psk:
        # User will not see this because they will be disconnected but we need to break here anyway
        return render_template('ap.html', message="Wrong password!")

    with open('wpa.conf', 'w') as f:
        f.write(wpa_conf % (ssid, pwd))
    with open('status.json', 'w') as f:
        f.write(json.dumps({'status':'disconnected'}))
    subprocess.Popen(["./disable_ap.sh"])
    return render_template('index.html', message="Please wait 2 minutes to connect.")

def is_wpa_setup() -> bool:
    """ Returns True if it is an initial run """
    return not os.path.isfile(WPA_CONF_PATH)

def setup_wpa_conf():
    with open(WPA_CONF_PATH, 'w') as f:
        f.write(wpa_conf_default)

if __name__ == "__main__":
    # things to run the first time it boots
    
    if not is_wpa_setup():
        setup_wpa_conf()
    
    # check connection
    if not is_connected():
        # subprocess.Popen("./enable_ap.sh")
        app.run(host="0.0.0.0", port=80, threaded=True)
    else:
        subprocess.Popen(STARTUP_SCRIPT)

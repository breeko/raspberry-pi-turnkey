import subprocess

import os
from utils import get_ssids, is_connected, check_cred, get_current_dir, create_network

from shutil import copyfile
from config import NAME

from flask import Flask, request, send_from_directory, jsonify, render_template, redirect
app = Flask(__name__, static_url_path='')


CURRENT_DIR = get_current_dir()

WPA_CONF_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"

TEMP_WPA_CONF_PATH = "{}/wpa_supplicant.conf".format(CURRENT_DIR)

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

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/signin', methods=['POST'])
def signin():
    ssid = request.form['ssid']
    password = request.form['password']

    print(ssid, password)
    valid_psk = check_cred(ssid, password)
    
    if not valid_psk:
        # User will not see this because they will be disconnected but we need to break here anyway
        return render_template('index.html', message="Wrong password!")

    with open(TEMP_WPA_CONF_PATH, 'a') as f:
        network = create_network(ssid = ssid, password = password)
        f.write(network)
    
    copyfile(TEMP_WPA_CONF_PATH, WPA_CONF_PATH)

    subprocess.Popen(["./disable_ap.sh"])
    return render_template('index.html', message="Please wait 2 minutes to connect.")

def is_wpa_setup() -> bool:
    """ Returns True if it is an initial run """
    return not os.path.isfile(WPA_CONF_PATH)

def setup_wpa_conf():
    with open(WPA_CONF_PATH, 'w') as f:
        f.write(wpa_conf_default)

def copy_wpa_conf():
    copyfile(WPA_CONF_PATH, TEMP_WPA_CONF_PATH)

if __name__ == "__main__":
    # things to run the first time it boots
    
    if not is_wpa_setup():
        setup_wpa_conf()
    
    copy_wpa_conf()

    # check connection
    if not is_connected():
        # subprocess.Popen("./enable_ap.sh")
        app.run(host="0.0.0.0", port=80, threaded=True)
    else:
        subprocess.Popen(STARTUP_SCRIPT)

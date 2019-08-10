import subprocess

import os
from utils import get_ssids, is_connected, check_cred, get_current_dir, create_network, restart_device

from shutil import copyfile

from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for
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
def main(message: str = None):
    message = message or "Configure your device by providing network information below"
    ssids = get_ssids(num_attempts = 15)
    return render_template('index.html', ssids=ssids, message=message)

# Captive portal when connected with iOS or Android
@app.route('/generate_204')
@app.route('/hotspot-detect.html')
@app.route('/ncsi.txt')
def redirect204():
    return redirect(url_for(main))

@app.route('/', methods=['POST'])
def signin():
    button_clicked = request.form.get("submit")
    if button_clicked == "restart":
        return restart_device(disable=True)
    elif button_clicked == "signin":
        return attempt_signin()

def attempt_signin():
    ssid = request.form['ssid']
    password = request.form['password']

    valid_psk = check_cred(ssid, password)
    
    if not valid_psk:
        return main("Incorrect password.")

    with open(TEMP_WPA_CONF_PATH, 'a') as f:
        network = create_network(ssid = ssid, password = password)
        f.write(network)
    
    copyfile(TEMP_WPA_CONF_PATH, WPA_CONF_PATH)

    return main("Success! Click restart to connect.")

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

    # TODO: Remove True
    if True or not is_connected():
        app.run(host="0.0.0.0", port=80, threaded=True)
    else:
        subprocess.Popen(STARTUP_SCRIPT)

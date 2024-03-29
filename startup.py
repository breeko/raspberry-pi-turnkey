import subprocess

import os
from utils import * # pylint: disable=unused-wildcard-import
from connection_utils import * # pylint: disable=unused-wildcard-import
from wpa_utils import * # pylint: disable=unused-wildcard-import

from constants import STARTUP_SCRIPT

from shutil import copyfile

from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for

app = Flask(__name__, static_url_path='')

@app.route('/')
def main(message: str = None):
    ssids = get_ssids(num_attempts = 15)
    network = get_connected_network()
    if network:
        ip_prefix = get_ip_prefix()
        ip_suffix = get_ip_suffix()
        return render_template('connected.html', restart=restart_device, message = message, network=network, ip_prefix=ip_prefix, ip_suffix=ip_suffix)
    else:
        return render_template('signin.html', restart=restart_device, ssids=ssids, message=message)

@app.route('/generate_204')
@app.route('/hotspot-detect.html')
@app.route('/ncsi.txt')
def redirect204():
    return redirect(url_for(main))

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/restart', methods=['GET'])
def restart():
    restart_device()
    return(main("Restarting..."))

@app.route('/', methods=['POST'])
def click():
    button_clicked = request.form.get("submit")
    print(request.form)
    if button_clicked == "signin":
        return attempt_signin()
    elif button_clicked == "setip":
        ip_suffix = request.form['input_ip_suffix']
        ip_prefix = get_ip_prefix()
        ip = ip_prefix + ip_suffix
        set_ip(ip_suffix = ip_suffix)
        reset_ip()
        return main("Static IP set to {}".format(ip))
    else:
        return main()

def attempt_signin():
    ssid = request.form['ssid']
    password = request.form['password']

    valid_psk = check_cred(ssid, password)
    if not valid_psk:
        return main("Incorrect password.")

    with open(WPA_CONF_PATH, 'a') as f:
        network = create_network(ssid = ssid, password = password)
        f.write(network)

    connect()

    return main("Success!")

if __name__ == "__main__":
    # things to run the first time it boots
    if not is_wpa_setup():
        setup_wpa_conf()

    # TODO: Remove True
    if True or not is_connected(include_shared=False):
        if not is_enabled():
            enable_app()
            restart_device()
        else:
            app.run(host="0.0.0.0", port=80, threaded=True, debug=True)
    else:
        if is_enabled():
            disable_app()
            restart_device()
        else:
            subprocess.Popen(STARTUP_SCRIPT)

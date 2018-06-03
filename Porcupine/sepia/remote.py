#
# S.E.P.I.A. remote actions 
# by Florian Quirin
#

import sys
import os
import requests
import json
import argparse

try:
    from .storage import Storage
except ValueError:
    raise ValueError("Please use 'python -m sepia.remote' (from outside the 'renote.py' folder) to start the main function of this module.")

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '/../respeaker/'))
    import respeaker.pixels
except ImportError:
    print("SEPIA remote: No LED supported.")

class Remote():
    """
    Class to do remote action calls to a SEPIA server.
    """

    def __init__(
            self,
            user_id,
            host_address = "",
            client_info = "wakeword_tool"):
        """
        Constructor.

        :param host_address: address of a SEPIA server, e.g. 'https://my.example.com:20726/sepia'.
        :param user_id: ID of a user to call server remote actions (needs to be authenticated).
        :param client_info: client name, e.g. wakeword_tool or python_app
        """
        self.storage = Storage()
        if not host_address:
            host_address = self.storage.get_default_host()
            if not host_address:
                raise ValueError('Missing SEPIA host address')

        self.host_address = host_address
        if not host_address.startswith("http"):
            self.host_address = "https://" + self.host_address
        if host_address.endswith("/"):
            self.host_address = self.host_address[:-1]

        self.client_info = client_info
        self.user_id = user_id
        self.user_data = self.storage.get_user_data(self.user_id)
        if not "token" in self.user_data:
            sys.exit("SEPIA remote: No user data found! Please generate a token first (python -m sepia.account --id=[sepia-user-id] --host=[sepia-server-url]).")
        if not "language" in self.user_data:
            self.user_data["language"] = "en"

        self.state = "idle"
        try:
            self.led = respeaker.pixels.Pixels()
        except NameError:
            self.led = None
        
    SENDING = "sending"
    LOADING = "loading"
    IDLE = "idle"
    SHUTTING_DOWN = "shutting_down"
    RECEIVED_SUCCESS = "received_success"
    RECEIVED_FAIL = "received_fail"

    def set_state(self, state_name):
        self.state = state_name
        if self.led:
            if self.state == Remote.IDLE:
                self.led.off()
            elif self.state == Remote.LOADING:
                self.led.wakeup()
                self.led.speak()
            elif self.state == Remote.SENDING:
                self.led.think()
            elif self.state == Remote.RECEIVED_SUCCESS:
                self.led.listen()
            elif self.state == Remote.RECEIVED_FAIL:
                self.led.speak()
            elif self.state == Remote.SHUTTING_DOWN:
                self.led.wakeup()
                self.led.speak()
            else:
                self.led.off()
        # print(self.state)


    def send_action(self, action_type, action, device="", channel=""):
        """
        Send remote action to server.
        """
        url = self.host_address + "/assist/remote-action"
        payload = {
            'type' : action_type,
            'action' : action,
            'client' : self.client_info,
            'channelId' : channel,
            'deviceId' : device,
            'KEY' : (self.user_id + ";" + self.user_data["token"])
        }
        headers = {
            'Content-Type': "application/x-www-form-urlencoded"
        }
        self.set_state(Remote.SENDING)
        response = requests.request("POST", url, data=payload, headers=headers)
        # print(response.text)    # DEBUG
        try:
            res = json.loads(response.text)
        except NameError:
            res = None
        if res and res["result"] and res["result"] == "success":
            self.set_state(Remote.RECEIVED_SUCCESS)
            return True
        else:
            print("SEPIA remote msg: " + response.text)
            self.set_state(Remote.RECEIVED_FAIL)
            return False

    def trigger_microphone(self, language="", device="", channel=""):
        """
        Send remote action: trigger microphone (on/off)
        """
        action_type = "hotkey"
        action = {
            "key": "F4", 
            "language": (language or self.user_data["language"])
        }
        return self.send_action(action_type, json.dumps(action), device, channel)  # note: we convert action to string


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='ID of user that wants to trigger a remote action', type=str)
    parser.add_argument('--action', help="Name of a pre-defined action, e.g. 'mic'", type=str)
    parser.add_argument('--host', help="Host address of SEPIA server, e.g. 'https://my.example.com/sepia'", type=str)
    args = parser.parse_args()

    if not args.id:
        raise ValueError('Missing user ID')
    if not args.action:
        raise ValueError('Missing action name')

    if not args.host:
        remote = Remote(user_id=args.id)
    else:
        remote = Remote(host_address=args.host, user_id=args.id)

    if args.action == "mic":
        remote.trigger_microphone()
    else:
        print("Action '" + args.action + "' not supported (yet?!)")
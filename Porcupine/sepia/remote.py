#
# S.E.P.I.A. remote actions 
# by Florian Quirin
#

import sys
import requests
import json
import argparse

from storage import Storage

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
            sys.exit("No user data found! Please generate a token first.")
        if not "language" in self.user_data:
            self.user_data["language"] = "en"
        

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
        response = requests.request("POST", url, data=payload, headers=headers)
        print(response.text)    # DEBUG

    def trigger_microphone(self, language="", device="", channel=""):
        """
        Send remote action: trigger microphone (on/off)
        """
        action_type = "hotkey"
        action = {
            "key": "F4", 
            "language": (language or self.user_data["language"])
        }
        self.send_action(action_type, json.dumps(action), device, channel)  # note: we convert action to string


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
#
# S.E.P.I.A. account handling 
# by Florian Quirin
#

import sys
import requests
import json
import getpass
import argparse

from storage import Storage

class Account():
    """
    Class to handle SEPIA accounts.
    """

    def __init__(
            self,
            host_address,
            user_id,
            client_info = "wakeword_tool"):
        """
        Constructor.

        :param host_address: address of a SEPIA server, e.g. 'https://my.example.com:20726/sepia'.
        :param user_id: ID of a user to manage.
        :param client_info: client name, e.g. wakeword_tool or python_app
        """
        self.host_address = host_address
        if not host_address.startswith("http"):
            self.host_address = "https://" + self.host_address
        if host_address.endswith("/"):
            self.host_address = self.host_address[:-1]
        
        self.storage = Storage()
        self.client_info = client_info
        self.user_id = user_id

    
    def authenticate(self, password):
        """
        Send authentication request to a SEPIA server and store basic data if successful.
        """
        url = self.host_address + "/assist/authentication"
        payload = {
            'action' : "validate",
            'client' : self.client_info,
            #'KEY' : (self.user_id + ";" + password)
            'GUUID' : self.user_id,
            'PWD' : password
        }
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        res = json.loads(response.text)

        if res["result"] and res["result"] == "success":
            # store result - overwrite any previous entries with same user ID
            self.storage.write_user_data(self.user_id, {
                "language" : res["user_lang_code"],
                "token" : res["keyToken"]
            })
            name = res["user_name"]["nick"] or res["user_name"]["first"]
            print("Success - " + name + ", your login token has been stored. Hf :-)")
            # store default host
            self.storage.write_default_host(self.host_address)
            print("Set (new) default host: " + self.host_address)
        else:
            print("Failed - I think the password is wrong or we got connection problems.")

    def check_login(self):
        """
        Send check request to a SEPIA server to see if the token is still valid.
        """
        # read token first
        user_data = self.storage.get_user_data(self.user_id)
        if not "token" in user_data:
            sys.exit("No user data found! Please generate a token first.")

        # check token
        token = user_data["token"]
        url = self.host_address + "/assist/authentication"
        payload = {
            'action' : "check",
            'client' : self.client_info,
            'KEY' : (self.user_id + ";" + token)
        }
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        res = json.loads(response.text)

        if res["result"] and res["result"] == "success":
            name = res["user_name"]["nick"] or res["user_name"]["first"]
            print("Success - Wb " + name + ", your login token is still valid.")
        else:
            print("Failed - I think the token is invalid or we got connection problems.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='ID of user that wants to trigger a remote action', type=str)
    parser.add_argument('--action', help="Name of a pre-defined account action, e.g. 'authenticate' or 'check'", type=str, default="authenticate")
    parser.add_argument('--host', help="Host address of SEPIA server, e.g. 'https://my.example.com/sepia'", type=str)
    parser.add_argument('--client', help="Client name, default: wakeword_tool", type=str, default="wakeword_tool")
    parser.add_argument('--pwd', help="Password for authentication. Use this only for testing please! The password will show in your console history!", type=str)
    args = parser.parse_args()

    if not args.id:
        raise ValueError('Missing user ID')
    if not args.host:
        if args.action == "authenticate":
            raise ValueError('Missing SEPIA host address')      # we do this to make sure we don't send the data to the wrong host

    account = Account(host_address=args.host, user_id=args.id, client_info=args.client)
    if not args.host:
        host = account.storage.get_default_host()
        if not host:
            raise ValueError('Missing SEPIA host address')      # now we need it because we got no default stored
        else:
            account.host_address = host

    if args.action == "authenticate":
        if args.pwd:
            account.authenticate(args.pwd)
        else:
            # ask for password using error stream (in case normal output is redirected) - Is that safe enough?
            p = getpass.getpass(stream=sys.stderr)
            account.authenticate(p)
    elif args.action == "check":
        account.check_login()
    else:
        print("Action '" + args.action + "' not supported (yet?!)")
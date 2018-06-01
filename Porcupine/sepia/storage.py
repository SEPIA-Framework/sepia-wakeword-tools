#
# S.E.P.I.A. local storage 
# by Florian Quirin
#

import pickle
import os.path
import argparse

class Storage():
    """
    Class to store and load SEPIA related data (like localStorage in Javascript).
    """

    def __init__(
            self,
            storage_path = "sepia_localstorage"):
        """
        Constructor.

        :param storage_path: path to the file that is used to store data.
        """
        self.storage_path = storage_path
        
        # create file if not exists
        if not os.path.isfile(self.storage_path):
            with open(self.storage_path, 'wb') as handle:
                pickle.dump({}, handle)

        self.data = {}

    def read(self, index):
        """
        Read data from storage.
        """
        with open(self.storage_path, 'rb') as handle:
            self.data = pickle.loads(handle.read())
            if self.data and index in self.data:
                return self.data[index]
            elif not self.data:
                self.data = {}
                return {}
            else:
                return {}

    def write(self, index, data):
        """
        Write data to storage.
        """
        self.read(index)   # refresh self.data (aka full_data)
        self.data[index] = data
            
        with open(self.storage_path, 'wb') as handle:
            pickle.dump(self.data, handle)

    def get_user_data(self, user_id):
        """
        Get user data for user ID from index 'users'.
        """
        users = self.read("users")
        if not user_id in users:
            return {}
        else:
            return users[user_id]
    
    def write_user_data(self, user_id, user_data):
        """
        Write user data for user ID to index 'users'.
        """
        users = self.read("users")
        users[user_id] = user_data
        self.write('users', users)

    def write_default_host(self, host_address):
        """
        Write default SEPIA host address.
        """
        self.write("host", host_address)

    def get_default_host(self):
        """
        Get default host address of SEPIA server.
        """
        return self.read("host")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--f', help="File that is used as storage (path and name)", type=str, default="sepia_localstorage")
    parser.add_argument('--o', help="Operation: 'read' or 'write'", type=str, default="read")
    parser.add_argument('--i', help="User-defined index to read from or write to, e.g. 'users'", type=str)
    parser.add_argument('--k', help="If you specify a key the data will be written to or read from this field inside the index", type=str)
    parser.add_argument('--d', help="Data to write. String will be evaluated", type=str)
    args = parser.parse_args()

    if not args.i:
        raise ValueError('Missing index')

    storage = Storage(storage_path=args.f)

    if args.o == "write":
        if not args.d:
            raise ValueError('Missing data')
        else:
            data = eval(args.d)
            if not args.k:
                storage.write(args.i, data)
            else:
                index_data = storage.read(args.i)
                index_data[args.k] = data
                storage.write(args.i, index_data)

            print ("DONE")
    else:
        index_data = storage.read(args.i)
        if not args.k:
            print(index_data)    
        else:
            if args.k in index_data:
                print(index_data[args.k])
            else:
                print("Not found")
        print ("DONE")

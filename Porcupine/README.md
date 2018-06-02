# Porcupine implementation for SEPIA wake-word trigger
This implementation uses the Porcupine wake-word (hotword, keyword) tool by [Picovoice](https://picovoice.ai/) to trigger SEPIA via the remote-actions endpoint.
It runs on x86 Linux, Windows and Mac with the custom keyword "Hey SEPIA" and on ARM Linux (Raspberry Pi) with the keywords included in the open-source package of Porcupine (e.g. "raspberry" or "grashopper" ^^).

# Quick-start

Requirements:
* Python (and python-dev I think)
* A couple of Python packages: pyaudio, numpy, enum34, soundfile, spidev (for LED support), requests
* A running SEPIA server
* A microphone, properly installed
* Detailed description coming soon ...

Clone this folder to your hard-drive and make sure your SEPIA server is running.

Open the folder and setup your SEPIA server and account first:

`python -m sepia.account --id=[sepia-user-id] --host=[sepia-server-url]` , e.g.:

`python -m sepia.account --id=uid1007 --host=my-sepia.example.com:20726/sepia` (Note the windows syntax: 'sepia\...')

You should see a confirmation that everything is ok.

Run the wake-word engine:

`python porcupine_sepia_remote.py --user_id=uid1007` (this will use the default Windows 'hey SEPIA' keyword, use -h for help)

Open your SEPIA client (Android app, browser, iOS, whatever uses the SEPIA WebSocket server for communication) and login with the same user you have just registered.
Say 'Hey SEPIA' and watch what happens :-) (the microphone in your app switches on ... hopefully).

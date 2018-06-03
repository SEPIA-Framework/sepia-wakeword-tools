import RPi.GPIO as GPIO
import time
import sys
import os
import argparse
from threading import Thread

import sepia.remote

class SepiaRespeakerButtonRemote(Thread):

    def __init__(self, user_id):
        super(SepiaRespeakerButtonRemote, self).__init__()

        self.BUTTON = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUTTON, GPIO.IN)

        # SEPIA setup
        self.state = 0  # 0: inactive, 1: ready, 2: waiting
        self.sepia_remote = sepia.remote.Remote(user_id = user_id)

    def normal_press(self):
        print("Normal press")
        self.state = 2
        if self.sepia_remote.trigger_microphone():
            print('SEPIA remote: triggered microphone')
        else:
            print('SEPIA remote: trigger failed')
        time.sleep(2)
        self.sepia_remote.set_state(self.sepia_remote.IDLE)
        self.state = 1

    def long_press(self):
        print("Long press")
        # GPIO.cleanup()
        # sys.exit()

    def max_press(self):
        print("Very long press")
        self.sepia_remote.set_state(self.sepia_remote.SHUTTING_DOWN)
        time.sleep(2)
        self.sepia_remote.set_state(self.sepia_remote.IDLE)
        time.sleep(2)
        GPIO.cleanup()
        self.state = 0

    def on_close(self):
        os.system("sudo shutdown -h now")
        # sys.exit()

    def run(self):
        self.state = 1
        try:
            # check normal, long and max. button press
            while self.state > 0:
                print("Waiting for button press")
                
                # wait for button signal (in this case we need falling edge)
                GPIO.wait_for_edge(self.BUTTON, GPIO.FALLING)
                #print(GPIO.input(self.BUTTON))

                # poll button at 20 Hz continuously for 5 seconds
                for i in range(101):
                    if GPIO.input(self.BUTTON) != 0:
                        break
                    time.sleep(0.05)
                # print(i)
                if i < 25:
                    self.normal_press()
                elif i < 100:
                    self.long_press()
                else:
                    self.max_press()

            self.on_close()

        except KeyboardInterrupt:
            # stop_recording()
            print("\nstopping...")
            GPIO.cleanup()       # clean up GPIO on CTRL+C exit


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user_id', help='User ID of SEPIA user to trigger remote action for.', type=str)
    args = parser.parse_args()

    if not args.user_id:
        raise ValueError('Missing user ID')

    SepiaRespeakerButtonRemote(
        user_id = args.user_id
    ).run()


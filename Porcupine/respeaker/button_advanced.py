import RPi.GPIO as GPIO
import time
import sys
import os

BUTTON = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON, GPIO.IN)

def normal_press():
    print("Normal press")

def long_press():
    print("Long press")
    # GPIO.cleanup()
    # sys.exit()

def max_press():
    print("Very long press")
    # GPIO.cleanup()
    # os.system("sudo shutdown -h now")
    # sys.exit()

try:
    # check normal, long and max. button press
    while True:
        print("Waiting for button press")
        
        # wait for button signal (in this case we need falling edge)
        GPIO.wait_for_edge(BUTTON, GPIO.FALLING)
        #print(GPIO.input(BUTTON))

        # poll button at 20 Hz continuously for 5 seconds
        for i in range(101):
            if GPIO.input(BUTTON) != 0:
                break
            time.sleep(0.05)

        # print(i)

        if i < 25:
            normal_press()
        elif i < 100:
            long_press()
        else:
            max_press()

except KeyboardInterrupt:
    # stop_recording()
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit

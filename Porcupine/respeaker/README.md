MIC HAT for Raspberry Pi (lite version for SEPIA)
=================================================

To build voice enabled projects.

[![](https://github.com/SeeedDocument/MIC_HATv1.0_for_raspberrypi/blob/master/img/mic_hatv1.0.png?raw=true)](https://www.seeedstudio.com/ReSpeaker-2-Mics-Pi-HAT-p-2874.html)


## Requirements
+ [seeed-voicecard](https://github.com/respeaker/seeed-voicecard), the kernel driver for on-board WM8960 codec
+ [spidev](https://pypi.python.org/pypi/spidev) for on-board SPI interface APA102 LEDs

## Setup
1. Go to [seeed-voicecard](https://github.com/respeaker/seeed-voicecard) and install it
2. Use `raspi-config` to enable SPI.
3. Install `spidev` (`pip install spidev`).
4. Run `python pixels.py` to test the pixels.

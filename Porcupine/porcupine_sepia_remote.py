#
# Copyright 2018 Picovoice Inc. - modified for S.E.P.I.A. by Florian Quirin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import os
import platform
import struct
import sys
import time
from datetime import datetime
from threading import Thread

import numpy as np
import pyaudio
import soundfile

import requests

import sepia.remote

sys.path.append(os.path.join(os.path.dirname(__file__), 'porcupine/binding/python/'))
from porcupine import Porcupine


class SepiaPorcupineRemote(Thread):
    """
    SEPIA remote action class for wake word detection based on Porcupine Python demo library. 
    It creates an input audio stream from a microphone, monitors it, upon detecting the specified wake word(s) prints the 
    detection time and index of wake word on console and sends the 'trigger microphone' remote action to the SEPIA server. 
    It optionally saves the recorded audio into a file for further review.
    """

    def __init__(
            self,
            library_path,
            model_file_path,
            keyword_file_paths,
            user_id,
            sensitivity=0.5,
            input_device_index=None,
            output_path=None,
            frame_length=0      # 0=auto
        ): 

        """
        Constructor.

        :param library_path: Absolute path to Porcupine's dynamic library.
        :param model_file_path: Absolute path to the model parameter file.
        :param keyword_file_paths: List of absolute paths to keyword files.
        :param sensitivity: Sensitivity parameter. For more information refer to 'include/pv_porcupine.h'. It uses the
        same sensitivity value for all keywords.
        :param input_device_index: Optional argument. If provided, audio is recorded from this input device. Otherwise,
        the default audio input device is used.
        :param output_path: If provided recorded audio will be stored in this location at the end of the run.
        """

        super(SepiaPorcupineRemote, self).__init__()

        self._library_path = library_path
        self._model_file_path = model_file_path
        self._keyword_file_paths = keyword_file_paths
        self._sensitivity = float(sensitivity)
        self._input_device_index = input_device_index
        self.frame_length = frame_length

        self._output_path = output_path
        if self._output_path is not None:
            self._recorded_frames = []

        # SEPIA setup
        self.state = 0  # 0: inactive, 1: listening, 2: waiting
        self.sepia_remote = sepia.remote.Remote(user_id = user_id)

    def run(self):
        """
         Creates an input audio stream, initializes wake word detection (Porcupine) object, and monitors the audio
         stream for occurrences of the wake word(s). It prints the time of detection for each occurrence and index of
         wake word and calls the SEPIA server for remote action 'trigger microphone'.
         """
        num_keywords = len(self._keyword_file_paths)
        self.state = 0   
        self.sepia_remote.set_state(self.sepia_remote.LOADING)
		
        def _audio_callback(in_data, frame_count, time_info, status):
            if frame_count >= porcupine.frame_length:
                pcm = struct.unpack_from("h" * porcupine.frame_length, in_data)
                result = porcupine.process(pcm)
                if self.state == 1:
                    if num_keywords == 1 and result:
                        print('[%s] detected keyword' % str(datetime.now()))
                        self.state = 2
                        if self.sepia_remote.trigger_microphone():
                            print('SEPIA remote: triggered microphone')
                        else:
                            print('SEPIA remote: trigger failed')
                        time.sleep(2)
                        self.sepia_remote.set_state(self.sepia_remote.IDLE)
                        self.state = 1
                    elif num_keywords > 1 and result >= 0:
                        print('[%s] detected keyword #%d' % (str(datetime.now()), result))
            
            return (None, pyaudio.paContinue)

        porcupine = None
        pa = None
        audio_stream = None
        try:
            porcupine = Porcupine(
                library_path=self._library_path,
                model_file_path=self._model_file_path,
                keyword_file_paths=self._keyword_file_paths,
                sensitivities=[self._sensitivity] * num_keywords)

            pa = pyaudio.PyAudio()
            sample_rate = porcupine.sample_rate
            num_channels = 1
            audio_format = pyaudio.paInt16
            if not self.frame_length:
                frame_length = porcupine.frame_length   # frame_length = 4096
            else:
                frame_length = self.frame_length
            audio_stream = pa.open(
                rate=sample_rate,
                channels=num_channels,
                format=audio_format,
                input=True,
                frames_per_buffer=frame_length,
                input_device_index=self._input_device_index,
				stream_callback=_audio_callback)

            audio_stream.start_stream()
            self.state = 1

            print("\nStarted porcupine with following settings:")
            if self._input_device_index:
                print("Input device: %d (check with --show_audio_devices_info)" % self._input_device_index)
            else:
                print("Input device: default (check with --show_audio_devices_info)")
            print("Sample-rate: %d" % sample_rate)
            print("Channels: %d" % num_channels)
            print("Format: %d" % audio_format)
            print("Frame-length: %d" % frame_length)
            print("Keyword file(s): %s" % self._keyword_file_paths)
            print("Waiting for keywords ...\n")
            
            self.sepia_remote.set_state(self.sepia_remote.IDLE)

            while True:
                time.sleep(0.1)

        except KeyboardInterrupt:
            print('\nstopping ...')
        finally:
            if audio_stream is not None:
                audio_stream.stop_stream()
                audio_stream.close()

            if porcupine is not None:
                porcupine.delete()

            if pa is not None:
                pa.terminate()

            if self._output_path is not None and len(self._recorded_frames) > 0:
                recorded_audio = np.concatenate(self._recorded_frames, axis=0).astype(np.int16)
                soundfile.write(self._output_path, recorded_audio, samplerate=sample_rate, subtype='PCM_16')

    _AUDIO_DEVICE_INFO_KEYS = ['index', 'name', 'defaultSampleRate', 'maxInputChannels']

    @classmethod
    def show_audio_devices_info(cls):
        """ Provides information regarding different audio devices available. """

        pa = pyaudio.PyAudio()

        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            print(', '.join("'%s': '%s'" % (k, str(info[k])) for k in cls._AUDIO_DEVICE_INFO_KEYS))

        pa.terminate()

def _default_library_path():
    system = platform.system()
    machine = platform.machine()

    if system == 'Darwin':
        return os.path.join(os.path.dirname(__file__), 'porcupine/lib/mac/%s/libpv_porcupine.dylib' % machine)
    elif system == 'Linux':
        if machine == 'x86_64' or machine == 'i386':
            return os.path.join(os.path.dirname(__file__), 'porcupine/lib/linux/%s/libpv_porcupine.so' % machine)
        else:
            raise Exception('Cannot autodetect library. Please use e.g.: --library_path="porcupine/lib/raspberry-pi/arm11/libpv_porcupine.so" (Pi Zero with ARM11 CPU).')
    elif system == 'Windows':
        if platform.architecture()[0] == '32bit':
            return os.path.join(os.path.dirname(__file__), 'porcupine\\lib\\windows\\i686\\libpv_porcupine.dll')
        else:
            return os.path.join(os.path.dirname(__file__), 'porcupine\\lib\\windows\\amd64\\libpv_porcupine.dll')
    raise NotImplementedError('Porcupine is not supported on %s/%s yet!' % (system, machine))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword_file_paths', help='Comma-separated absolute paths to keyword files. Default is "hey_sepia_windows.ppn".', 
        type=str, default='porcupine/keyword_files/hey_sepia_windows.ppn')
    parser.add_argument('--library_path', help='Path to Porcupine library, e.g.: --library_path="porcupine/lib/raspberry-pi/arm11/libpv_porcupine.so" (Pi Zero with ARM11 CPU).',
        type=str)
    parser.add_argument('--model_file_path', help='Path to model parameter file.',
        type=str, default=os.path.join(os.path.dirname(__file__), 'porcupine/lib/common/porcupine_params.pv'))
    parser.add_argument('--sensitivity', help='Detection sensitivity [0, 1]', default=0.5)
    parser.add_argument('--input_audio_device_index', help='Index of input audio device (same as --input_device).', type=int, default=None)   # we keep this for compatability
    parser.add_argument('--input_device', help='Index of input audio device (check with --show_audio_devices_info).', type=int, default=None)
    parser.add_argument('--frame_length', help='Frame length setting for audio buffer. On Pi Zero you might want to try --frame_length=4096.', type=int, default=0)
    parser.add_argument('--output_path', help='Path to where recorded audio will be stored. If not set, it will be bypassed.',
        type=str, default=None)
    parser.add_argument('--show_audio_devices_info', help='Show a list of devices to be used with --input_device.', action='store_true')
    parser.add_argument('--user_id', help='User ID of SEPIA user to trigger remote action for.', type=str)

    args = parser.parse_args()

    if args.show_audio_devices_info:
        SepiaPorcupineRemote.show_audio_devices_info()
    else:
        if not args.keyword_file_paths:
            raise ValueError('Keyword file paths are missing')
        if not args.user_id:
            raise ValueError('Missing user ID')

        input_device = None     # default
        if args.input_audio_device_index:
            input_device = args.input_audio_device_index
        elif args.input_device:
            input_device = args.input_device

        SepiaPorcupineRemote(
            library_path=args.library_path if args.library_path is not None else _default_library_path(),
            model_file_path=args.model_file_path,
            keyword_file_paths=[x.strip() for x in args.keyword_file_paths.split(',')],
            sensitivity=args.sensitivity,
            output_path=args.output_path,
            input_device_index=input_device,
            frame_length=args.frame_length,
            user_id = args.user_id
        ).run()

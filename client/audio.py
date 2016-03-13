import pyaudio as pa

import sys
sys.path.append('../common/')

from settings import SAMPLE_WIDTH, NUM_CHANNELS, FRAME_RATE, FRAMES_PER_PACKET
from client_settings import BLOCK_SIZE, gStartFlag
from utils import create_zeros

import wave  #TEMP

pyaudio = None
input_stream = None
output_stream = None

output_queue = []
input_queue = []

TEMP_INSTRUMENT_WAVE_DATA = wave.open('./songs/lamprey/drums.wav', 'rb')


def in_callback(in_data, frame_count, time_info, status):
    if gStartFlag:
        frames = TEMP_INSTRUMENT_WAVE_DATA.readframes(FRAMES_PER_PACKET)
        input_queue.append(frames)
    
    # if len(in_data):
    #     input_queue.append(in_data)  #need to chunk
    return ('', pyaudio.paContinue)


def out_callback(in_data, frame_count, time_info, status):
    out_data = create_zeros(frame_count)
    if len(output_queue):
        out_data = output_queue.pop(0)
    return (out_data, pyaudio.paContinue)


def init():
    global pyaudio, input_stream, output_stream

    pyaudio = pa.PyAudio()

    input_stream = pyaudio.open(
        format=pa.get_format_from_width(SAMPLE_WIDTH),
        channels=NUM_CHANNELS,
        rate=FRAME_RATE,
        input=True,
        frames_per_buffer=BLOCK_SIZE,
        stream_callback=in_callback)
    input_stream.start_stream()

    output_stream = pyaudio.open(
        format=pa.get_format_from_width(SAMPLE_WIDTH),
        channels=NUM_CHANNELS,
        rate=FRAME_RATE,
        output=True,
        frames_per_buffer=BLOCK_SIZE,
        stream_callback=out_callback)
    output_stream.start_stream()


def close():
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    pyaudio.terminate()

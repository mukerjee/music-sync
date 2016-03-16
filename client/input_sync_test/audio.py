import pyaudio as pa

import sys
sys.path.append('../../common/')

from utils import create_zeros, get_chunks
from settings import SAMPLE_WIDTH, NUM_CHANNELS, FRAME_RATE, \
    FRAMES_PER_PACKET, FRAME_WIDTH
from client_settings import BLOCK_SIZE

pyaudio_obj = None
stream = None

output_queue = []
input_queue = []

output_start_time = 0


def callback(in_data, frame_count, time_info, status):
    global output_start_time
    seq_num = 0
    for i, frames in enumerate(get_chunks(in_data,
                                          FRAMES_PER_PACKET * FRAME_WIDTH)):
        if output_start_time == 0:
            continue
        sample_gap = 1.0 / FRAME_RATE
        packet_time = time_info['input_buffer_adc_time'] + \
                      (i * sample_gap * FRAMES_PER_PACKET) - \
                      output_start_time - stream.get_input_latency()
        seq_num = int(packet_time / (FRAMES_PER_PACKET * sample_gap))
        if seq_num >= 0:
            input_queue.append((seq_num, frames))
    
    out_data = create_zeros(frame_count)
    if len(output_queue):
        if output_start_time == 0:
            output_start_time = time_info['output_buffer_dac_time']
        sample_gap = 1.0 / FRAME_RATE
        osn, ose, out_data = output_queue.pop(0)
    return (out_data, pa.paContinue)


def init():
    global pyaudio_obj, stream

    pyaudio_obj = pa.PyAudio()

    stream = pyaudio_obj.open(
        format=pa.get_format_from_width(SAMPLE_WIDTH),
        channels=NUM_CHANNELS,
        rate=FRAME_RATE,
        input=True,
        output=True,
        frames_per_buffer=BLOCK_SIZE,
        stream_callback=callback)
    stream.start_stream()


def close():
    stream.stop_stream()
    stream.close()
    pyaudio_obj.terminate()

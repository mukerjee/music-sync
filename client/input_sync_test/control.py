import wave

import audio
from player import Player

import sys
sys.path.append('../../common/')

from utils import get_chunks, mix
from settings import FRAMES_PER_PACKET, FRAME_WIDTH
from client_settings import BACKING_FNs, BLOCK_SIZE

seq_num = 0
players = []

input_audio_packets = {}


def run():
    global seq_num
    end = seq_num + BLOCK_SIZE / FRAMES_PER_PACKET
    data = []
    volumes = []
    if end in players[0].audio_packets:
        for player in players:
            d = ''
            for i in xrange(seq_num, end):
                d += player.audio_packets[i]
            data.append(d)
            volumes.append(player.volume)

        audio.output_queue.append((seq_num, end, mix(data, volumes)))
        seq_num = end


def init():
    for i, fn in enumerate(BACKING_FNs):
        p = Player(i+1)
        players.append(p)
        p.volume = 1.0
        data_file = wave.open(fn, 'rb')
        data = data_file.readframes(data_file.getnframes())
        sequence_number = 0
        for d in get_chunks(data, FRAMES_PER_PACKET * FRAME_WIDTH):
            p.audio_packets[sequence_number] = d
            sequence_number += 1


def close():
    dump_file = wave.open('test_out.wav', 'w')
    dump_file.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
    
    while len(audio.input_queue):
        seq, data = audio.input_queue.pop(0)
        input_audio_packets[seq] = data

    to_write = []
        
    for seq in sorted(input_audio_packets.keys()):
        volumes = [p.volume for p in players]
        data = [p.audio_packets[seq] for p in players]

        volumes.append(10.0)
        data.append(input_audio_packets[seq])

        to_write.append(mix(data, volumes))
    dump_file.writeframes(''.join(to_write))
    dump_file.close()

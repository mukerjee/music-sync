import wave

import network
import audio
import gui
from player import Player

import sys
sys.path.append('../common/')

from utils import parse_raw_data, mix, create_audio_packet, parse_raw_cmds, \
    create_zeros, get_chunks
from settings import FRAMES_PER_PACKET, FRAME_WIDTH, FRAME_RATE
from client_settings import BACKING_FNs, BLOCK_SIZE, STARTUP_DELAY
from cmds import run_cmd

import globals

scode = {'start': 'strt', 'player': 'plyr', 'instrument': 'inst'}
local_cmds = ['volume']

last_network_seq_num = -1


def audio_mix():
    if globals.StartFlag:
        end = globals.OutputSequenceNumber + BLOCK_SIZE / FRAMES_PER_PACKET
        data = []
        volumes = []
        for player in globals.Players:
            d = ''
            for i in xrange(globals.OutputSequenceNumber, end):
                d += player.audio_packets[i]
            data.append(d)
            volumes.append(player.volume)

        globals.OutputSequenceNumber = end
        audio.output_queue.append(mix(data, volumes))


def parse_audio_from_server():
    global last_network_seq_num
    while len(network.input_audio_queue):
        rawData, _ = network.input_audio_queue.pop(0)
        seq, soundData = parse_raw_data(rawData)
        if seq > last_network_seq_num + 100:
            continue
        last_network_seq_num = seq
        if soundData:
            if globals.PlayerID > 1:
                globals.previousPlayer.audio_packets[
                    seq] = soundData
                globals.MaxServerSeqNumber = \
                    max(seq, globals.MaxServerSeqNumber)
                if globals.MaxServerSeqNumber > STARTUP_DELAY * \
                   FRAME_RATE / FRAMES_PER_PACKET:
                    globals.StartFlag = True


def send_audio_to_server():
    while len(audio.input_queue):
        seq_num, frames = audio.input_queue.pop(0)
        packet = create_audio_packet(seq_num, frames)
        network.output_audio_queue.append(packet)


def parse_user_cmd():
    while len(gui.output_mesg_queue):
        mesg = gui.output_mesg_queue.pop(0)
        if mesg[0] == '/':
            mesg = mesg.split(' ')
            lcode = mesg[0][1:]
            data = ''.join(mesg[1:]) if len(mesg) > 1 else ''
            if lcode in local_cmds:
                run_cmd(lcode, data)
            else:
                code = scode[lcode] if lcode in scode else lcode
                network.output_cmd_queue.append("%s %s\n" % (code, data))
        else:
            network.output_cmd_queue.append("mesg %s\n" % mesg)


def process_cmds():
    if len(network.input_cmd_buffer):
        cmds, leftover = parse_raw_cmds(network.input_cmd_buffer)
        network.input_cmd_buffer = leftover
        for code, data in cmds:
            run_cmd(code, data)


def run(obj):
    parse_user_cmd()
    process_cmds()
    send_audio_to_server()
    parse_audio_from_server()
    audio_mix()
    

def init():
    for i, fn in enumerate(BACKING_FNs):
        p = Player(i+1)
        globals.Players.append(p)
        data_file = wave.open(fn, 'rb')
        data = data_file.readframes(data_file.getnframes())
        sequence_number = 0
        for d in get_chunks(data, FRAMES_PER_PACKET * FRAME_WIDTH):
            #TODO: this implies you can't switch order of instruments
            p.audio_packets[sequence_number] = d
            sequence_number += 1
    
    packet = create_audio_packet(-1, create_zeros(FRAMES_PER_PACKET))
    network.output_audio_queue.append(packet)


def close():
    pass

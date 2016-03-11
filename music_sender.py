#!/usr/bin/env python

import wave
import time

import socket

from pydub import AudioSegment

MP3_BUFFER = 65536
CHUNK = 256
SERVER_IP = '10.0.1.18'  # '71.206.246.146'
TCP_PORT = 12346
UDP_PORT = 12345


drums = wave.open('./Drums2.wav', 'rb')


udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.connect((SERVER_IP, TCP_PORT))

seq = 0


def getData():
    #data = drums.readframes(MP3_BUFFER)
    data = drums.readframes(CHUNK)
    return data
    # if data == '':
    #     return ''
    # output = wave.open('./temp.wav', 'wb')
    # output.setparams((2, 2, 44100, 0, 'NONE', 'NONE'))
    # output.writeframes(data)
    # output.close()
    # wav_audio = AudioSegment.from_file('./temp.wav', format='wav')
    # wav_audio.export('./temp.mp3', format='mp3')
    # return './temp.mp3'


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def sendAudio(data):
    global seq
    # print fn
    # if fn == 'zeros':
    #     data = ''.join([chr(0x00)] * MP3_BUFFER * 2 * 2)
    # else:
    #     data = open(fn).read()
    # print seq, len(data)
    #data = list(chunks(data, CHUNK * 2 * 2))
    data = [data]
    for d in data:
        udp.sendto(str(seq) + chr(0x00) + d, (SERVER_IP, UDP_PORT))
        print seq
        seq += 1

for i in xrange(100):
    zeros = ''.join([chr(0x00)] * CHUNK * 2 * 2)
    sendAudio(zeros)
    time.sleep(CHUNK * 0.5 / 44100)

tcp.send('start: ' + str(seq))
while True:
    sendAudio(getData())
    #d_data = drums.readframes(CHUNK)
    time.sleep(CHUNK * 0.5 / 44100)

#!/usr/bin/env python

import pyaudio
import wave
import numpy
import socket
import time

CHUNK = 256
FRAME_SIZE = 1024

LOCAL_ADDR = '10.0.1.18'
TCP_PORT = 12346
UDP_PORT = 12345

fns = ['./Violin2.wav', './Piano2.wav']  # , './Bass2.wav', './Drums2.wav']
backing = [wave.open(fn, 'rb') for fn in fns]
backing_data = [b.readframes(FRAME_SIZE) for b in backing]

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.setblocking(False)
udp.bind((LOCAL_ADDR, UDP_PORT))

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.setblocking(False)
tcp.bind((LOCAL_ADDR, TCP_PORT))
tcp.listen(10)

subframe = {}
start_flag = False
cur_seq = 0

p = pyaudio.PyAudio()


def mix(samples):
    for i in xrange(len(samples)):
        samples[i] = numpy.fromstring(samples[i], numpy.int16)
        samples[i] *= 1.0 / len(samples)
    #print len(samples[0]), len(samples[1])
    return sum(samples).tostring()
    

def callback(in_data, frame_count, time_info, status):
    global cur_seq, backing_data
    data = ''.join([chr(0x00)] * frame_count * 2 * 2)
    end = cur_seq + FRAME_SIZE / CHUNK
    if start_flag and end in subframe:
        frame = []
        for i in xrange(cur_seq, end):
            while True:
                j = i
                if j in subframe:
                    frame.append(subframe[j])
                    break
                else:
                    j -= 1
                if j < cur_seq:
                    frame.append(''.join([chr(0x00)] * CHUNK * 2 * 2))
                    break
        frame = [subframe[i] for i in xrange(cur_seq, end)]
        frame = ''.join(frame)
        cur_seq = end
        data = mix([frame] + backing_data)
        backing_data = [b.readframes(FRAME_SIZE) for b in backing]
    return (data, pyaudio.paContinue)

stream = p.open(format=p.get_format_from_width(backing[0].getsampwidth()),
                channels=backing[0].getnchannels(),
                rate=backing[0].getframerate(),
                output=True,
                stream_callback=callback)

stream.start_stream()

while True:
    try:
        conn, addr = tcp.accept()
        break
    except:
        pass

while stream.is_active():
    try:
        mesg = conn.recv(200)
        if mesg != '':
            print mesg
        if mesg[:5] == 'start':
            seq = int(mesg[7:])
            start_flag = True
            cur_seq = seq
            print cur_seq
            #frames = []
    except:
        pass

    while True:
        try:
            soundData, addr = udp.recvfrom(CHUNK * 2 * 2 * 2)
            print addr
            for i in xrange(len(soundData)):
                if soundData[i] == chr(0x00):
                    break
            seq = int(soundData[:i])
            soundData = soundData[i+1:]
            subframe[seq] = soundData
            # if len(subframe) >= FRAME_SIZE / CHUNK:
            #     frames.append(''.join(subframe))
            #     subframe = []
        except:
            break
    time.sleep(0.0001)

print 'done'
stream.stop_stream()
stream.close()
conn.shutdown(socket.SHUT_RDWR)
conn.close()
tcp.close()
udp.close()
for b in backing:
    b.close()

p.terminate()

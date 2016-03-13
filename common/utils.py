import numpy as np
from select import select

from settings import NUM_CHANNELS, SAMPLE_WIDTH


def read_until_block(s):
    mesg = ''
    while len(read_select(s)):
        m = s.recv(2048)
        if not len(m):  # client closed connection
            return mesg
        mesg += m
    return mesg


def recv_from_until_block(s):
    packets = []
    while len(read_select(s)):
        packets.append(s.recvfrom(2048))
    return packets


def read_select(s):
    return select([s], [], [], 0)[0]


def write_select(s):
    return select([], [s], [], 0)[1]


def parse_raw_data(rawData):
    seq = 0
    soundData = ''
    i = rawData.find(chr(0x00))
    if i != -1:
        seq = int(rawData[:i])
        soundData = rawData[i+1:]
    return (seq, soundData)


# Yield successive n-sized chunks from l.
def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

        
# takes in a list of equal length binary strings of sample data. mixes equally
def mix(list_of_samples):
    ls = list_of_samples
    for i in xrange(len(ls)):
        ls[i] = np.fromstring(ls[i], np.int16)
        ls[i] = (1.0 / len(ls)) * ls[i].astype(np.float64)
        ls[i] = ls[i].astype(np.int16)
    return sum(ls).tostring()


def create_zeros(num_frames):
    return ''.join([chr(0x00)] * num_frames * NUM_CHANNELS * SAMPLE_WIDTH)


def parse_raw_cmds(cmd_buffer):
    raw_cmds = cmd_buffer.split('\n')
    leftover = raw_cmds[-1]
    raw_cmds = raw_cmds[:-1]
    cmds = []
    for raw_cmd in raw_cmds:
        code = raw_cmd[:4]
        data = raw_cmd[5:] if len(raw_cmd) > 5 else ''
        cmds.append(code, data)
    return cmds, leftover


def create_audio_packet(seq_num, data):
    return '%s%s%s' % (str(seq_num), chr(0x00), data)

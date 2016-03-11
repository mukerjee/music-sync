from select import select

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


import wave
from client_settings import gStartFlag, gAudioPackets, \
    gInputSequenceNumber, gOutputSequenceNumber

scode = {'start': 'strt', 'player': 'plyr', 'instrument': 'inst'}

fns = ['./songs/lamprey/drums.wav', './songs/lamprey/bass.wav',
       './songs/lamprey/piano.wav', './songs/lamprey/violin.wav']


def parse_audio():
    while len(network.input_audio_queue):
        rawData, _ in network.input_audio_queue.pop(0)
        seq, soundData = parse_raw_data(rawData)
        if soundData:
            gAudioPackets[seq].append(soundData)


def audio_mix():
    global gOutputSequenceNumber
    if gStartFlag:
        end = gOutputSequenceNumber + BLOCK_SIZE / FRAMES_PER_PACKET
        frames = ''
        for i in xrange(gOutputSequenceNumber, end):
            frames += mix(gAudioPackets[i].values())
        gOutputSequenceNumber = end
        audio.output_queue.append(frames)


def send_audio_to_server():
    global gInputSequenceNumber
    while len(audio.input_queue):
        frames = audio.input_queue.pop(0)
        packet = create_audio_packet(gInputSequenceNumber, frames)
        network.output_audio_queue.append(packet)
        gInputSequenceNumber += 1


def parse_user_cmd():
    while len(gui.output_mesg_queue):
        mesg = gui.output_mesg_queue.pop(0)
        if mesg[0] == '/':
            i = mesg.find(' ')
            if i != -1:
                lcode = mesg[1:i]
                data = mesg[i+1:]
                code = scode[lcode] if lcode in scode else lcode
                network.output_cmd_queue.append("%s %s \n" % (code, data))
        else:
            network.output_cmd_queue.append("mesg %s \n" % instance.text)


def run_cmd():
    global network.input_cmd_buffer, gui.chat_box
    if len(network.input_cmd_buffer):
        cmds, leftover = parse_raw_cmds(network.input_cmd_buffer)
        network.input_cmd_buffer = leftover
        for code, data in cmds:
            run_cmd(code, data)


def run():
    parse_user_cmd()
    run_cmd()
    parse_audio()
    audio_mix()
    send_audio_to_server()
    

def init():
    for i, fn in enumerate(fns):
        data_file = wave.open(fn, 'rb')
        data = data_file.readframes(data_file.getnframes())
        sequence_number = 0
        for audio in chunks(data, FRAMES_PER_PACKET):
            gAudioPackets[sequence_number][i] = audio
            sequence_number += 1
    
    packet = create_audio_packet(-1, create_zeros(FRAMES_PER_PACKET))
    network.output_audio_queue.append(packet)


def close():
    pass

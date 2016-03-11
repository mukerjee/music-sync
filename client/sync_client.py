#!/usr/local/bin/kivy

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.clock import Clock

import socket
from select import select
from functools import partial

import pyaudio
import wave
import numpy

SERVER_IP = '128.2.214.18' #'10.0.1.18'  # '71.206.246.146'
TCP_PORT = 2688
UDP_PORT = 2688
data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

chat_box = None
buffer = ''

CHUNK = 256
FRAME_SIZE = 1024

fns = ['./Violin2.wav', './Piano2.wav']  # , './Bass2.wav', './Drums2.wav']
backing = [wave.open(fn, 'rb') for fn in fns]
backing_data = [b.readframes(FRAME_SIZE) for b in backing]

subframe = {}
start_flag = False
cur_send_seq = 0
cur_listen_seq = 0

audio_buffer = []
sub_frame = []
server_subframes = {}


def mix(samples):
    for i in xrange(len(samples)):
        samples[i] = numpy.fromstring(samples[i], numpy.int16)
        samples[i] = (1.0 / len(samples)) * samples[i].astype(numpy.float64)
        samples[i] = samples[i].astype(numpy.int16)
    return sum(samples).tostring()


Builder.load_string('''
<ScrollableLabel>:
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
''')


class ScrollableLabel(ScrollView):
    text = StringProperty('')


def refocus_ti(instance, *largs):
    instance.focus = True
       

scode = {'start': 'strt', 'player': 'plyr', 'instrument': 'inst'}

my_inst_data = None


def on_enter(instance):
    global my_inst_data
    if instance.text:
        if instance.text[0] == '/':
            m = instance.text[1:].split(' ')
            lcode = m[0]
            data = ' '.join(m[1:])
            code = scode[lcode] if lcode in scode else lcode
            control_socket.send(code + ' ' + data + '\n')

            if code == 'inst':
                    if data == 'drums':
                            my_inst_data = wave.open('./Drums2.wav', 'rb')
        else:
            control_socket.send("mesg " + instance.text + '\n')
        instance.text = ""
        instance.focus = True
        Clock.schedule_once(partial(refocus_ti, instance))


class TempoWindow(GridLayout):

    def __init__(self, **kwargs):
        global chat_box
        super(TempoWindow, self).__init__(**kwargs)
        self.cols = 1
        chat_box = ScrollableLabel(text='Welcome')
        self.add_widget(chat_box)
        textinput = TextInput(text='', multiline=False)
        textinput.bind(on_text_validate=on_enter)
        self.add_widget(textinput)


class MyApp(App):

    def build(self):
        return TempoWindow()


def reader_poll(obj):
    global buffer, start_flag, cur_send_seq, cur_listen_seq
    ready = select([control_socket], [], [], 0)
    for r in ready[0]:
        buffer += r.recv(1024)
    if len(buffer):
        p = buffer.find('\n')
        if p != -1:
            mesg = buffer[:p]
            buffer = buffer[p+1:]
            code = mesg[:4]
            data = mesg[5:]
            if code == 'mesg':
                p = data.find(' ')
                if p != -1:
                    nick = data[:p]
                    m = data[p+1:]
                    chat_box.text += ('\n' + nick + ": " + m)
            if code == 'strt':
                print 'starting'
                start_flag = True
                cur_send_seq = 0
                cur_listen_seq = 0


def callback(in_data, frame_count, time_info, status):
    global cur_listen_seq, backing_data
    data = ''.join([chr(0x00)] * frame_count * 2 * 2)
    if start_flag:
        if my_inst_data:
            my_data = my_inst_data.readframes(FRAME_SIZE)
            audio_buffer.append(my_data)
            data = mix([my_data] + backing_data)

        else:
            end = cur_listen_seq + FRAME_SIZE / CHUNK
            if end in server_subframes:
                frame = []
                for i in xrange(cur_listen_seq, end):
                    subframe = ''.join([chr(0x00)] * CHUNK * 2 * 2)
                    for j in xrange(i, cur_listen_seq - 1, -1):
                        if j in server_subframes:
                            subframe = server_subframes[j]
                            break
                    frame.append(subframe)
                frame = ''.join(frame)
                data = mix([frame] + backing_data)
            else:
                data = mix(backing_data)
            cur_listen_seq = end
        backing_data = [b.readframes(FRAME_SIZE) for b in backing]
    return (data, pyaudio.paContinue)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def sendAudio(obj):
    global cur_send_seq, audio_buffer, sub_frame
    ready = select([], [data_socket], [], 0)[1]
    while len(ready):
        if len(sub_frame):
            d = sub_frame.pop(0)
            data_socket.sendto(str(cur_send_seq) + chr(0x00) + d,
                               (SERVER_IP, UDP_PORT))
            cur_send_seq += 1
        else:
            if len(audio_buffer):
                sub_frame = list(chunks(audio_buffer.pop(0), CHUNK * 2 * 2))
            else:
                zeros = ''.join([chr(0x00)] * CHUNK * 2 * 2)
                data_socket.sendto(str(-1) + chr(0x00) + zeros,
                                   (SERVER_IP, UDP_PORT))
                return
        ready = select([], [data_socket], [], 0)[1]


def recvAudio(obj):
    ready = select([data_socket], [], [], 0)[0]
    while len(ready):
        soundData, _ = data_socket.recvfrom(2048)
        for i in xrange(len(soundData)):
            if soundData[i] == chr(0x00):
                break
        seq = int(soundData[:i])
        soundData = soundData[i+1:]
        #print 'got drum data: ', str(seq), str(cur_listen_seq), len(soundData)
        server_subframes[seq] = soundData
        ready = select([data_socket], [], [], 0)[0]



if __name__ == '__main__':
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(backing[0].getsampwidth()),
                    channels=backing[0].getnchannels(),
                    rate=backing[0].getframerate(),
                    output=True,
                    stream_callback=callback)

    stream.start_stream()
    control_socket.connect((SERVER_IP, TCP_PORT))
    print 'connected'

    Clock.schedule_interval(reader_poll, 0.002)
    Clock.schedule_interval(sendAudio, 0.002)
    Clock.schedule_interval(recvAudio, 0.002)
    MyApp().run()

    print 'done'
    stream.stop_stream()
    stream.close()
    for b in backing:
        b.close()

    p.terminate()



# while stream.is_active():
#     try:
#         mesg = conn.recv(200)
#         if mesg != '':
#             print mesg
#         if mesg[:5] == 'start':
#             seq = int(mesg[7:])
#             start_flag = True
#             cur_seq = seq
#             print cur_seq
#     except:
#         pass

#     while True:
#         try:
#             soundData, addr = udp.recvfrom(CHUNK * 2 * 2 * 2)
#             print addr
#             for i in xrange(len(soundData)):
#                 if soundData[i] == chr(0x00):
#                     break
#             seq = int(soundData[:i])
#             soundData = soundData[i+1:]
#             subframe[seq] = soundData
#         except:
#             break
#     time.sleep(0.0001)

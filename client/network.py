import socket

import sys
sys.path.append('../common/')

from settings import CONTROL_PORT, DATA_PORT
from utils import write_select, recv_from_until_block
from client_settings import SERVER_IP

data_socket = None
control_socket = None

output_cmd_queue = []
input_cmd_buffer = ''

output_audio_queue = []
input_audio_queue = []


def send():
    while len(output_cmd_queue):
        while len(write_select(control_socket)):
            cmd = output_cmd_queue.pop(0)
            control_socket.send(cmd)

    while len(output_audio_queue):
        while len(write_select(data_socket)):
            packet = output_audio_queue.pop(0)
            data_socket.sendto(packet, (SERVER_IP, DATA_PORT))


def recv():
    global input_cmd_buffer, input_audio_queue
    input_cmd_buffer += recv_from_until_block(control_socket)
    input_audio_queue += recv_from_until_block(data_socket)
    

def run(obj):
    send()
    recv()


def init():
    global data_socket, control_socket
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_socket.connect((SERVER_IP, CONTROL_PORT))


def close(control_socket, data_socket):
    control_socket.close()
    data_socket.close()

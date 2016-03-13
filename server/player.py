import sys
sys.path.append('../common/')

from utils import parse_raw_cmds


class Player():
    def __init__(self, control_socket, addr):
        self.control_socket = control_socket
        self.addr = addr
        self.data_port = -1
        
        self.nick = addr
        self.id = -1
        self.ready = False
        self.instrument = None

        self.input_cmd_buffer = ''
        self.output_cmd_queue = []
        self.output_data_queue = []

        self.input_audio = {}

    def get_cmds(self):
        cmds, leftover = parse_raw_cmds(self.input_cmd_buffer)
        self.input_cmd_buffer = leftover
        return cmds

#!/usr/bin/env python

import socket

from select import select

FRAMES_PER_PACKET = 256
FRAME_WIDTH = 4

LOCAL_ADDR = '0.0.0.0'
CONTROL_PORT = 2688
DATA_PORT = 2688

#TODO: Do this at the client with buffering
#START_DELAY = 2.0

running = True


def run_cmd(code, player, data):
    return {
        'strt': cmd_start,
        'stop': cmd_stop,
        'goto': cmd_goto,
        'load': cmd_load,
        'inst': cmd_instrument,
        'nick': cmd_nick,
        'mesg': cmd_mesage,
        'plyr': cmd_player,
        'redy': cmd_ready,
    }.get(code, cmd_error)(player, data)


class Player():
    def __init__(self, control_socket, addr):
        self.control_socket = control_socket
        self.addr = addr
        self.data_port = -1
        
        self.nick = addr
        self.id = -1
        self.ready = False
        self.instrument = None

        #TODO
        self.dirty = True

        self.input_cmd_buffer = ''
        self.output_cmd_queue = []
        self.output_data_queue = []

        self.input_audio = {}

    def get_cmds(self):
        cmds = self.input_cmd_buffer.split('\n')
        self.input_cmd_buffer = cmds[-1]
        return cmds[:-1]
    
#TODO: Implement
location = 0
song = 0

players = []
playing = False

data_port_for_addr = {}


def s_mesg(m):
    for player in players:
        player.output_cmd_queue.append('mesg *server* %s\n' % m)


def check_listen():
    global players
    if len(select([control_listen], [], [], 0)[0]):
        control_socket, (addr, port) = control_listen.accept()
        print 'control: %s connected' % addr
        players.append(Player(control_socket, addr))


def read_from_control_sockets():
    for player in players:
        ready = select([player.control_socket], [], [], 0)[0]
        while len(ready):
            mesg = player.control_socket.recv(1024)
            if len(mesg) == 0:
                #TODO: client closed connection
                break
            ready = select([player.control_socket], [], [], 0)[0]


def process_control_messages():
    for player in players:
        for cmd in player.get_cmds():
            code = cmd[:4]
            data = cmd[5:] if len(cmd) > 5 else ''
            run_cmd(code, player, data)


def cmd_start(player, data):
    global playing
    playing = True
    for p in players:
        p.input_audio = {}
        p.output_data_queue = []
        p.output_cmd_queue.append('strt\n')
    s_mesg('%s starts the song' % player.nick)
            

def cmd_stop(player, data):
    global playing
    playing = False
    for p in players:
        p.output_cmd_queue.append('stop\n')
    s_mesg('%s stops the song' % player.nick)


def cmd_goto(player, data):
    #TODO
    s_mesg('%s sets time to...' % player.nick)


def cmd_load(player, data):
    #TODO
    s_mesg('%s loads song...' % player.nick)


def cmd_instrument(player, data):
    #TODO
    s_mesg('%s set to %s' % (player.nick, data))


def cmd_nick(player, data):
    n = player.nick
    player.nick = data[:-1]
    s_mesg('%s changed name to %s' % (n, player.nick))


def cmd_mesage(player, data):
    for p in players:
        p.output_cmd_queue.append("mesg %s %s\n" % (player.nick, data))


def cmd_player(player, data):
    new_id = int(data)
    other_player = None
    for p in players:
        if p.id == new_id:
            other_player = p

    old_id = player.id
    player.id = new_id
    s_mesg('%s set to player %d' % (player.nick, new_id))

    if other_player:
        other_player.id = old_id
        if old_id != -1:
            s_mesg('%s set to player %d' % (other_player.nick, old_id))
        else:
            s_mesg('%s removed from play' % other_player.nick)

    for p in players:
        p.ready = False
        p.dirty = True


def cmd_ready(player, data):
    if player.id != -1 and not player.dirty:
        player.ready = True

        for p in players:
            p.dirty = True
        s_mesg("%s's body is ready" % player.nick)


def cmd_error(player, data):
    s_mesg('%s issued a bad command' % (player.nick))


def send_to_control_sockets():
    for player in players:
        ready = select([], [player.control_socket], [], 0)[1]
        while len(ready):
            #TODO: move this into the output cmd queue?
            if player.id != -1 and player.dirty:
                #player.control_socket.send(get_state())
                player.dirty = False

            while len(player.output_cmd_queue):
                cmd = player.output_cmd_queue.pop(0)
                player.control_socket.send(cmd)

            ready = select([], [player.control_socket], [], 0)[1]
    

def control(control_listen):
    check_listen(control_listen)
    read_from_control_sockets()
    process_control_messages()
    send_to_control_sockets()


# def get_state():
#     mesg = 'stat '
#     for d in dirty_state:
#         mesg += 1 if d else 0
#     mesg += ' '
#     for r in player_ready:
#         mesg += 1 if r else 0
#     mesg += ' '
#     mesg += 1 if playing else 0
#     mesg += ' '
#     mesg += location
#     mesg += ' '
#     mesg += song
#     mesg += '\n'
#     return mesg

def read_from_data_sockets(data_socket):
    ready = select([data_socket], [], [], 0)[0]
    while len(ready):
        # need to account for sequence numbers
        rawData, (addr, port) = data_socket.recvfrom(FRAMES_PER_PACKET
                                                     * FRAME_WIDTH * 2)
        player = None
        for p in players:
            if p.addr == addr:
                p.data_port = port
                player = p

        if player:
            i = rawData.find(chr(0x00))
            if i != -1:
                seq = int(rawData[:i])
                soundData = rawData[i+1:]
                player.input_audio[seq] = soundData

                for p in players:
                    if p.id == player.id + 1:
                        # add sample to next player's queue
                        p.output_data_queue.append(rawData)

        ready = select([data_socket], [], [], 0)[0]


def send_to_data_sockets(data_socket):
    for player in players:
        ready = select([], [data_socket], [], 0)[1]
        while playing and len(ready) and len(player.output_data_queue):
            data_socket.sendto(player.output_data_queue,
                               (player.addr, player.data_port))
            ready = select([], [data_socket], [], 0)[1]
    

def data(data_socket):
    read_from_data_sockets(data_socket)
    send_to_data_sockets(data_socket)


def shutdown(control_listen, data_socket):
    for player in players:
        player.control_socket.shutdown(socket.SHUT_RDWR)
        player.control_socket.close()
    control_listen.close()
    data_socket.close()
    print 'done shutdown'


if __name__ == '__main__':
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_socket.bind((LOCAL_ADDR, DATA_PORT))

    control_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    control_listen.bind((LOCAL_ADDR, CONTROL_PORT))
    control_listen.listen(10)

    while running:
        control(control_listen)
        data(data_socket)
    shutdown(control_listen, data_socket)

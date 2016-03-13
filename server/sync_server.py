#!/usr/bin/env python

import socket

import sys
sys.path.append('../common/')

from player import Player
from cmds import run_cmd
from utils import read_until_block, recv_from_until_block, \
    read_select, write_select, parse_raw_data
from settings import CONTROL_PORT, DATA_PORT
from server_settings import LOCAL_ADDR, gRunning, gPlayers, gPlaying


def check_listen():
    global gPlayers
    if len(read_select(control_listen)):
        control_socket, (addr, port) = control_listen.accept()
        gPlayers.append(Player(control_socket, addr))
        print 'control: %s connected' % addr


def read_from_control_sockets():
    for player in gPlayers:
        mesg = read_until_block(player.control_socket)
        if not len(mesg):  # client closed connection
            gPlayers.remove(player)
        else:
            player.input_cmd_buffer.append(mesg)


def process_control_messages():
    for player in gPlayers:
        for cmd in player.get_cmds():
            code, data = cmd
            run_cmd(code, player, data)


def send_to_control_sockets():
    for player in gPlayers:
        while len(player.output_cmd_queue):
            while len(write_select(player.control_socket)):
                cmd = player.output_cmd_queue.pop(0)
                player.control_socket.send(cmd)
    

def read_from_data_sockets(data_socket):
    packets = recv_from_until_block(data_socket)
    for rawData, (addr, port) in packets:
        player = None
        for p in gPlayers:
            if p.addr == addr:
                p.data_port = port
                player = p

        if player:
            seq, soundData = parse_raw_data(rawData)
            if soundData:
                player.input_audio[seq] = soundData
                for p in gPlayers:
                    if p.id == player.id + 1:
                        # add sample to next player's queue
                        p.output_data_queue.append(rawData)


def send_to_data_sockets(data_socket):
    for player in gPlayers:
        while gPlaying and len(write_select(data_socket)) and \
              len(player.output_data_queue):
            rawData = player.output_data_queue.pop(0)
            data_socket.sendto(rawData, (player.addr, player.data_port))
    

def shutdown(control_listen, data_socket):
    for player in gPlayers:
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

    while gRunning:
        check_listen(control_listen)
        read_from_control_sockets()
        process_control_messages()
        send_to_control_sockets()

        read_from_data_sockets(data_socket)
        send_to_data_sockets(data_socket)
    shutdown(control_listen, data_socket)

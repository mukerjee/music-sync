import gui
import network
import audio
import control

import globals
from player import Player


def run_cmd(code, data):
    print '%s %s' % (code, data)
    return {
        'strt': cmd_start,
        'mesg': cmd_mesg,
        'inst': cmd_inst,
        'plyr': cmd_player,
        'volume': cmd_volume,
    }.get(code, cmd_error)(data)


def cmd_start(data):
    control.input_audio_queue = []
    control.last_network_seq_num = -1
    gui.input_mesg_queue = []
    gui.output_mesg_queue = []
    audio.output_queue = []
    audio.input_queue = []
    network.output_cmd_queue = []
    network.input_cmd_buffer = ''
    network.output_audio_queue = []
    network.input_audio_queue = []
    
    globals.OutputSequenceNumber = 0
    globals.InputSequenceNumber = 0
    globals.MaxServerSeqNumber = -1
    if globals.PlayerID == 1:
        globals.StartFlag = True


def cmd_mesg(data):
    p = data.find(' ')
    if p != -1:
        nick = data[:p]
        m = data[p+1:]
        gui.input_mesg_queue.append('%s: %s\n' % (nick, m))


def cmd_inst(data):
    globals.Instrument = data

    
def cmd_player(data):
    old_id = globals.PlayerID
    for i, p in enumerate(globals.Players):
        if p.id == old_id:
            globals.Players.remove(p)
            globals.Players.append(Player(old_id))

    globals.PlayerID = int(data)

    for i, p in enumerate(globals.Players):
        if p.id == globals.PlayerID:
            globals.Players.remove(p)
            globals.myPlayer = Player(globals.PlayerID)
            globals.Players.append(globals.myPlayer)

        if p.id == globals.PlayerID - 1:
            globals.Players.remove(p)
            globals.previousPlayer = Player(globals.PlayerID - 1)
            globals.Players.append(globals.previousPlayer)

    globals.myPlayer.volume = 0.0
    

def cmd_volume(data):
    data = data.split(' ')
    if len(data) > 1:
        pid = int(data[0])
        v = float(data[1])
        for p in globals.Players:
            if p.id == pid:
                p.volume = v
    

def cmd_error(data):
    print 'received bad command from the server'

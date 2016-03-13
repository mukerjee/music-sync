import gui

from client_settings import gStartFlag, gInputSequenceNumber, \
    gOutputSequenceNumber


def run_cmd(code, data):
    return {
        'strt': cmd_start,
        'mesg': cmd_mesg,
    }.get(code, cmd_error)(data)


def cmd_start(data):
    global gStartFlag, gInputSequenceNumber, gOutputSequenceNumber
    print 'starting'
    gStartFlag = True
    gOutputSequenceNumber = 0
    gInputSequenceNumber = 0


def cmd_mesg(data):
    p = data.find(' ')
    if p != -1:
        nick = data[:p]
        m = data[p+1:]
        gui.chat_box.text += ('\n' + nick + ": " + m)


def cmd_error(data):
    print 'received bad command from the server'
    pass

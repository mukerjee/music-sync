import globals


def s_mesg(m):
    for player in globals.Players:
        player.output_cmd_queue.append('mesg *server* %s\n' % m)


def run_cmd(code, player, data):
    print '%s: %s %s' % (code, player.nick, data)
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


def cmd_start(player, data):
    global playing
    playing = True
    for p in globals.Players:
        p.input_audio = {}
        p.output_data_queue = []
        p.output_cmd_queue.append('strt\n')
    s_mesg('%s starts the song' % player.nick)
            

def cmd_stop(player, data):
    global playing
    playing = False
    for p in globals.Players:
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
    player.output_cmd_queue.append("inst %s\n" % data)
    s_mesg('%s set to %s' % (player.nick, data))


def cmd_nick(player, data):
    n = player.nick
    player.nick = data
    s_mesg('%s changed name to %s' % (n, player.nick))


def cmd_mesage(player, data):
    for p in globals.Players:
        p.output_cmd_queue.append("mesg %s %s\n" % (player.nick, data))


def cmd_player(player, data):
    new_id = int(data)
    other_player = None
    for p in globals.Players:
        if p.id == new_id:
            other_player = p

    old_id = player.id
    player.id = new_id
    s_mesg('%s set to player %d' % (player.nick, new_id))
    player.output_cmd_queue.append("plyr %d\n" % player.id)

    if other_player:
        other_player.id = old_id
        if old_id != -1:
            s_mesg('%s set to player %d' % (other_player.nick, old_id))
        else:
            s_mesg('%s removed from play' % other_player.nick)
        other_player.output_cmd_queue.append("plyr %d\n" % old_id)

    for p in globals.Players:
        p.ready = False
        #p.output_cmd_queue(get_state())


def cmd_ready(player, data):
    if player.id != -1:
        player.ready = True

        for p in globals.Players:
            #p.output_cmd_queue(get_state())
            pass
        s_mesg("%s's body is ready" % player.nick)


def cmd_error(player, data):
    s_mesg('%s issued a bad command' % player.nick)

class Player():
    def __init__(self, id):
        self.nick = id
        self.id = id
        self.ready = False

        self.instrument = None
        self.volume = 1.0

        self.audio_packets = {}

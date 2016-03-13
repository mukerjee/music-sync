from collections import defaultdict

BLOCK_SIZE = 1024

SERVER_IP = '128.2.214.18' #'10.0.1.18'  # '71.206.246.146'

gStartFlag = False
gInputSequenceNumber = 0
gOutputSequenceNumber = 0

# Maps sequence number to an instrument id to audio
gAudioPackets = defaultdict(lambda: defaultdict(str))

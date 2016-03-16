#!/usr/bin/env python

import time

import audio
import control

if __name__ == '__main__':
    audio.init()
    control.init()

    for i in xrange(20000):
        control.run()
        time.sleep(0.0002)

    control.close()
    audio.close()

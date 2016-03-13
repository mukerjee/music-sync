#!/usr/local/bin/kivy
from kivy.clock import Clock

import audio
import network
import gui
import control

if __name__ == '__main__':
    audio.init()
    network.init()
    control.init()

    Clock.schedule_interval(control.run, 0.0002)
    Clock.schedule_interval(network.run, 0.0002)
    gui.run()

    control.close()
    network.close()
    audio.close()

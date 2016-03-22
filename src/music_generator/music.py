import time
import rtmidi as rt
from random import randint

scale = [58, 60, 62, 63, 65, 67, 69, 70]

def play_bars(n, bpm):
    # play n bars in sequence from scale
    bps = bpm / 60.0
    eighth = 1.0 / (2.0 * bps) # seconds

    midiout = rt.MidiOut()
    ports = midiout.get_ports()
    midiout.open_port(1)
    print "Connected"

    count = 0
    bars = 0
    
    while bars < n:
        i = randint(0, len(scale) - 1)
        k = randint(1, 4)
        m = randint(1, k)
        p = randint(0, 1)
        #p = 1
        
        if count % 8 == 0:
            i = 0

        note  = scale[i] - p * 12 - 1
        other = scale[(i + 2) % len(scale)] - p * 12 - 1
        yes   = scale[(i + 4) % len(scale)] - p * 12 - 1
        
        if count % 2 == 0:
            velocity = 127
        else:
            velocity = 20
        
        if count + k > 7:
            k = 7 - count
            count = 0
            bars += 1
        else:
            count += k

        midiout.send_message([0x90, note, velocity])
        midiout.send_message([0x90, other, velocity])
        midiout.send_message([0x90, yes, velocity])
        time.sleep(eighth * m)
        midiout.send_message([0x80, note, 0])
        midiout.send_message([0x80, other, 0])
        midiout.send_message([0x80, yes, 0])

        if k > m:
            time.sleep(eighth * (k - m))
        
    del midiout

from __future__ import print_function
# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

# Test of note blocks.
# Create three rows of noteblocks, tuned according to a random tone-row, and triggered by tripwires.
# As entities move around in the arena, they will play notes.
# Noteblocks use a different instrument sound depending on the block they sit on top of.
# Note that they need an air block directly above them in order to sound.
# For best results, adjust your Minecraft sound options - put Noteblocks on 100% and reduce everything else.

from builtins import range
try:
    from malmo import MalmoPython
except:
    import MalmoPython
import json
import math
import os
import random
import sys
import time
import numpy as np
import csv

from collections import defaultdict


class TranslationError(Exception):
    '''Error raised if frequency does not have a noteblock translation'''
    def __init__(self, t, f):
        self.t = t
        self.f = f
        super().__init__()

    def __str__(self):
        return "The frequency " + str(self.f) + " at time " + str(self.t) + " does not map to a noteblock in minecraft"


def translate_to_noteblock_number(freq_dict) -> dict:
    '''Takes frequencies and translates to noteblock numbers'''
    BLOCK_TRANSLATION = {
        184.997: "F_sharp_3",
        195.998: "G3",
        207.652: "G_sharp_3",
        220: "A3",
        233.082: "A_sharp_3",
        246.941: "B3",
        261.625: "C4",
        277.182: "C_sharp_4",
        293.664: "D4",
        311.127: "D_sharp_4",
        329.627: "E4",
        349.228: "F4",
        369.994: "F_sharp_4",
        391.995: "G4",
        415.304: "G_sharp_4",
        439.999: "A4",
        466.163: "A_sharp_4",
        493.883: "B4",
        523.25: "C4",
        554.365: "C_sharp_5",
        587.329: "D5",
        622.253: "D_sharp_5",
        659.254: "E5",
        698.455: "F5",
        739.988: "F_sharp_5"
    }
    noteblock_dict = defaultdict(str)
    for time, freq in freq_dict.items():
        if freq not in BLOCK_TRANSLATION:
            raise TranslationError(time, freq)
        noteblock_dict[time] = BLOCK_TRANSLATION[freq]
    return noteblock_dict

data = open('songs/Scales.csv','r')
data_reader = csv.reader(data)
line_num = 0
frequencies = []
max_freq_dict = {}
for row in data_reader:
    row = [float(i) for i in row]
    if line_num == 0:
        frequencies = row
    ### TODO: Make a better converter
    elif line_num >= 2 and (line_num-6) % 50 == 0: ## 50 because a quarter note = 0.50 seconds in 118 BPM
        max_freq_dict[line_num] = frequencies[row.index(max(row))]
    line_num +=1

translated_dict = translate_to_noteblock_number(max_freq_dict)
pitches = []
for note in translated_dict.values():
    pitches.append(note)
    pitches.append('0')
    pitches.append('0')
    pitches.append('0')
pitches = np.reshape(pitches,(-1,16))
agent_start_pos_x = 0.5
agent_start_pos_y = 2
agent_start_pos_z = 0.5

def initNoteblocks(pitches):
    # Create Row for sound 
    tone_row = np.reshape(pitches,(-1,16))
    tone_row1 = tone_row[0].tolist()
    # Reverse Second Half since it's going backwards  
    tone_row2 = tone_row[1].tolist()[::-1]
    xml = ""
    # Draw the noteblocks:
    # TODO: pass in an array of size 16 into this function to determine which notes are being played at what timing.
    for i in range(1,17):
        if tone_row1[i-1] == '0':
            xml+= '''<DrawBlock x="0" y="2" z="{z}" type="stone"/>'''.format(z=(i*2)+1)
        else:
            xml += '''<DrawBlock x="0" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'''.format(z=(i*2)+1, pitch = tone_row1[i-1])
            xml += '''<DrawBlock x="0" y="1" z="{z}" type="{type}"/>'''.format(z=(i*2)+1,type="planks")

        if tone_row2[i-1] == '0':
            xml+= '''<DrawBlock x="2" y="2" z="{z}" type="stone"/>'''.format(z=(i*2)+1)
        else:
            xml += '''<DrawBlock x="2" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'''.format(z=(i*2)+1, pitch = tone_row2[i-1])
            xml += '''<DrawBlock x="2" y="1" z="{z}" type="{type}"/>'''.format(z=(i*2)+1,type="planks")

    for k in range(1,18):
        if k != 17:
            xml += '<DrawBlock x="2" y="2" z="{z}" type="unpowered_repeater" face="SOUTH"/>'.format(z=(k*2))
        xml += '<DrawBlock x="0" y="2" z="{z}" type="unpowered_repeater" face="NORTH"/>'.format(z=(k*2))
        xml += '<DrawBlock x="0" y="2" z="1" type="wooden_pressure_plate" />'
        

    xml += '''<DrawLine x1="0" x2="2" y1="2" y2="2" z1="35" z2="35" type="redstone_wire"/>
            <DrawBlock x="2" y="2" z="34" type="redstone_wire"/>
            <DrawLine x1="2" x2="4" y1="2" y2="2" z1="1" z2="1" type="redstone_wire"/>
            <DrawBlock x="4" y="2" z="2" type="redstone_wire"/>'''
    
    return xml

def addNoteblocks(pitches, currX):
    # Create Row for sound   
    tone_row = np.reshape(pitches,(-1,16))
    tone_row1 = tone_row[0].tolist()
    # Reverse Second Half since it's going backwards  
    tone_row2 = tone_row[1].tolist()[::-1]
    xml = ""
    # Draw the noteblocks:
    for i in range(1,17):
        if tone_row1[i-1] == '0': 
            xml+= '<DrawBlock x="{x}" y="2" z="{z}" type="stone"/>'.format(x=currX,z=(i*2)+1)
        else:
            xml += '<DrawBlock x="{x}" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'.format(x=currX, z=(i*2)+1, pitch = tone_row1[i-1])
            xml += '<DrawBlock x="{x}" y="1" z="{z}" type="{type}"/>'.format(x=currX, z=(i*2)+1, type="dirt")
        
        if tone_row2[i-1] == '0':
            xml += '<DrawBlock x="{x2}" y="2" z="{z}" type="stone"/>'.format(x2=currX+2,z=(i*2)+1)
        else:
            xml += '<DrawBlock x="{x2}" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'.format(x2=currX+2, z=(i*2)+1, pitch = tone_row2[i-1])
            xml += '<DrawBlock x="{x2}" y="1" z="{z}" type="{type}"/>'.format(x2=currX+2,z=(i*2)+1,type="dirt")

    for k in range(1,18):
        if k != 17:
            xml += '<DrawBlock x="{x2}" y="2" z="{z}" type="unpowered_repeater" face="SOUTH"/>'.format(x2=currX+2, z=(k*2))
        if k > 1:
            xml += '<DrawBlock x="{x}" y="2" z="{z}" type="unpowered_repeater" face="NORTH"/>'.format(x=currX, z=(k*2))
        

    xml += '''<DrawLine x1="{x}" x2="{x2}" y1="2" y2="2" z1="35" z2="35" type="redstone_wire"/>
              <DrawLine x1="{x2}" x2="{x3}" y1="2" y2="2" z1="1" z2="1" type="redstone_wire"/>
              <DrawBlock x="{x3}" y="2" z="2" type="redstone_wire"/>
              <DrawBlock x="{x2}" y="2" z="34" type="redstone_wire"/>'''.format(x=currX, x2=currX+2, x3=currX+4)

    return xml


missionXML = '''<?xml version="1.0" encoding="UTF-8" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <About>
            <Summary>Studio Session</Summary>
        </About>

        <ServerSection>
            <ServerInitialConditions>
                <Weather>clear</Weather>
            </ServerInitialConditions>
            <ServerHandlers>
                <FlatWorldGenerator generatorString="3;7,2;1;" />
                <DrawingDecorator>''' + initNoteblocks(pitches[:2]) + addNoteblocks(pitches[2:4],4) + '''</DrawingDecorator>
                <ServerQuitFromTimeUp timeLimitMs="1000000" />
                <ServerQuitWhenAnyAgentFinishes />
            </ServerHandlers>
        </ServerSection>

        <AgentSection mode="Survival">
            <Name>LilSteve</Name>
            <AgentStart>
                <Placement x="0.5" y="2.0" z="-0.5"/>
            </AgentStart>
            <AgentHandlers>
                <ObservationFromFullStats/>
                <ContinuousMovementCommands turnSpeedDegs="420"/>
            </AgentHandlers>
        </AgentSection>
    </Mission>'''

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)
my_mission = MalmoPython.MissionSpec(missionXML,True)
agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print('ERROR:',e)
    print(agent_host.getUsage())
    exit(1)
if agent_host.receivedArgument("help"):
    print(agent_host.getUsage())
    exit(0)

my_mission_record = MalmoPython.MissionRecordSpec()
max_retries = 3
for retry in range(max_retries):
    try:
        agent_host.startMission( my_mission, my_mission_record )
        break
    except RuntimeError as e:
        if retry == max_retries - 1:
            print("Error starting mission",e)
            print("Is the game running?")
            exit(1)
        else:
            time.sleep(2)

world_state = agent_host.peekWorldState()
while not world_state.has_mission_begun:
    time.sleep(0.3)
    world_state = agent_host.peekWorldState()

# Loop until mission ends:
while world_state.is_mission_running:
    print(".", end="")
    #agent_host.sendCommand("move 1")
    agent_host.sendCommand("move 1")
    agent_host.sendCommand("move 1")
    time.sleep(0.1)
    world_state = agent_host.getWorldState()
    for error in world_state.errors:
        print("Error:",error.text)

print()
print("Mission ended")
# Mission has ended.

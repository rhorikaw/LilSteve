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
import pandas as pd
import csv
import xml.etree.ElementTree as ET
from scipy.signal import find_peaks
from sklearn.ensemble import RandomForestClassifier
from collections import defaultdict


BLOCK_TRANSLATION = {
    46.249: "F_sharp_3",
    48.999: "G3",
    51.913: "G_sharp_3",
    55: "A3",
    58.270: "A_sharp_3",
    61.735: "B3",
    65.406: "C4",
    69.296: "C_sharp_4",
    73.416: "D4",
    77.782: "D_sharp_4",
    82.407: "E4",
    87.307: "F4",
    92.499: "F_sharp_4",
    97.999: "G4",
    103.826: "G_sharp_4",
    110: "A4",
    116.541: "A_sharp_4",
    123.471: "B4",
    130.813: "C5",
    138.591: "C_sharp_5",
    146.832: "D5",
    155.563: "D_sharp_5",
    164.814: "E5",
    174.614: "F5",
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
    523.25: "C5",
    554.365: "C_sharp_5",
    587.329: "D5",
    622.253: "D_sharp_5",
    659.254: "E5",
    698.455: "F5",
    739.988: "F_sharp_5"
}

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
    noteblock_dict = defaultdict(str)
    for time, freq in freq_dict.items():
        if freq not in BLOCK_TRANSLATION:
            raise TranslationError(time, freq)
        noteblock_dict[time] = BLOCK_TRANSLATION[freq]
    return noteblock_dict

def get_note_from_XML(instrument_mod, pitch, alter, octave):
    notes = ["C", "D", "E", "F", "G", "A", "B"]
    new_octave = octave
    if pitch == "G" and octave == 5:
        new_octave -= 1
    mod_octave = instrument_mod + int(new_octave)
    note = notes[int(notes.index(pitch)) + int(alter)]
    if alter == -1:
        return "{p}_sharp_{o}".format(p=note, o=mod_octave)
    elif alter == 1:
        return "{p}_sharp_{o}".format(p=pitch, o=mod_octave)
    else:
        return "{p}{o}".format(p=pitch, o=mod_octave)

## Parse XML
def get_pitches_from_XML(filename):
    piano_notes = []
    bass_notes  = []
    tree = ET.parse(filename)
    root = tree.getroot()
    for child in root[2]:
        # print(child.tag)
        for gran in child:
            if gran.tag == "note":
                if gran[2].tag == "tie":
                    gran.remove(gran[2])
                # print(gran[2].text)
                if int(gran[2].text) == 2:
                    if gran[0].tag == "chord":
                        bass_notes[-1] = get_note_from_XML(2, gran[0][0].text, int(gran[0][1].text), int(gran[0][2].text))
                    if gran[0].tag == "rest":
                        for i in range(int(gran[1].text)//6):
                                bass_notes.append("0")
                    else:
                        bass_notes.append(get_note_from_XML(2, gran[0][0].text, int(gran[0][1].text), int(gran[0][2].text)))
                        for i in range((int(gran[1].text)//6) - 1):
                            bass_notes.append("0")
                elif int(gran[2].text) == 1:
                    if gran[0].tag == "chord":
                        gran.remove(gran[0])
                    if gran[0].tag == "rest":
                        for i in range(int(gran[1].text)//6):
                                piano_notes.append("0")
                    else:
                        piano_notes.append(get_note_from_XML(-1, gran[0][0].text, int(gran[0][1].text), int(gran[0][2].text)))
                        for i in range((int(gran[1].text)//6) - 1):
                            piano_notes.append("0")
    piano_notes = np.array(piano_notes, dtype=object)
    bass_notes = np.array(bass_notes, dtype=object)
    bass_notes = np.where(bass_notes=="G5", "G4", bass_notes )
    return (piano_notes, bass_notes)

sixteenth_note_value = 10  ### 60/ (4*BPM)
frequencies = []
forest_data_dict = {}
max_freq_dict = {}
## Generate Training Data
files = ["Superstition.csv", "Scale+Beat.csv", "Scales.csv", "Training Data.csv"]
for file_name in files:
    if file_name == "Scales.csv":
        sixteenth_note_value = 12.5
    forest_data = []
    data = open(file_name, 'r')
    data_reader = csv.reader(data)
    line_num = 0
    note_index = 0
    max_amp = 0
    for row in data_reader:
        row = [float(i) for i in row]
        if line_num == 0:
            frequencies = row
        ### TODO: Make a better converter
        ### Approximate 16th notes
        elif line_num >= 2 and (line_num-6) == round(sixteenth_note_value*note_index): ## 50 because a quarter note = 0.50 seconds in 118 BPM
            if max_amp < max(row):
                max_amp = max(row)
            forest_data.append(row)
            note_index += 1
        line_num +=1
    data.close()
    forest_data_dict[max_amp] = forest_data
modified_forest_data = []
for maxa in forest_data_dict:
    np_data = np.array(forest_data_dict[maxa])/maxa
    modified_forest_data.extend(np_data.tolist())

# Generate Test Data
test_X = []
datas = open("SevenNationArmy.csv", 'r')
data_reader = csv.reader(datas)
line_num = 0
note_index = 0
max_amp = 0
for row in data_reader:
    row = [float(i) for i in row]
    if line_num == 0:
        frequencies = row
    elif line_num >= 2 and (line_num-6) == round(sixteenth_note_value*note_index): 
        if max_amp < max(row):
            max_amp = max(row)
        test_X.append(row)
        note_index += 1
    line_num +=1
datas.close()
temp = test_X[0:32]
temp.extend(test_X[160:192])
train_X = np.array(temp)/max_amp
modified_forest_data.extend(train_X)
test_X = np.array(test_X)/max_amp

df = pd.read_excel("train_Y.xlsx") 
piano_Y = df.Piano.to_numpy()
bass_Y = df.Bass.to_numpy()
kick_Y = df.Kick.to_numpy()
snare_Y = df.Snare.to_numpy()
hat_Y = df.Hat.to_numpy()

dfT = pd.read_excel("sna_Y.xlsx")
piano_YT = dfT.Piano.to_numpy()
bass_YT = dfT.Bass.to_numpy()
kick_YT = dfT.Kick.to_numpy()
snare_YT = dfT.Snare.to_numpy()
hat_YT = dfT.Hat.to_numpy()

RFC_piano = RandomForestClassifier()
RFC_piano.fit(modified_forest_data, piano_Y)
test_piano_Y = RFC_piano.predict(test_X)

RFC_bass = RandomForestClassifier()
RFC_bass.fit(modified_forest_data, bass_Y)
test_bass_Y = RFC_bass.predict(test_X)

RFC_kick = RandomForestClassifier()
RFC_kick.fit(modified_forest_data, kick_Y)
test_kick_Y = RFC_kick.predict(test_X)

RFC_snare = RandomForestClassifier()
RFC_snare.fit(modified_forest_data, snare_Y)
test_snare_Y = RFC_snare.predict(test_X)

RFC_hat = RandomForestClassifier()
RFC_hat.fit(modified_forest_data, hat_Y)
test_hat_Y = RFC_hat.predict(test_X)

piano_acc = 1 - sum(np.absolute(test_piano_Y-piano_YT))/len(piano_YT)
bass_acc = 1 - sum(np.absolute(test_bass_Y-bass_YT))/len(bass_YT)
kick_acc = 1 - sum(np.absolute(test_kick_Y-kick_YT))/len(kick_YT) 
snare_acc = 1 - sum(np.absolute(test_snare_Y-snare_YT))/len(snare_YT) 
hat_acc = 1 - sum(np.absolute(test_hat_Y-hat_YT))/len(hat_YT)
overall_acc = np.average([piano_acc, bass_acc, kick_acc, snare_acc, hat_acc])

print("Note Accuracies:\n\tPiano: {p_a}% \n\tBass: {b_a}% \n\tKick: {k_a}% \n\tSnare: {s_a}% \n\tHat: {h_a}% \n\n\tOverall: {o_a}%".format( 
    p_a = piano_acc*100,
    b_a = bass_acc*100, 
    k_a = kick_acc*100, 
    s_a = snare_acc*100, 
    h_a = hat_acc*100,
    o_a = overall_acc*100))


def convert_for_malmo(test_piano_Y, test_bass_Y, test_kick_Y, test_snare_Y, test_hat_Y ):
    piano, bass = get_pitches_from_XML('SevenNationArmy.xml')
    kick = []
    snare = []
    hat = []
    for i in range(len(test_piano_Y)):
        if test_piano_Y[i] == 0:
            piano[i] = "0"
        if test_bass_Y[i] == 0:
            bass[i] = "0"
        if test_kick_Y[i] == 1:
            kick.append("F_sharp_3")
        else:
            kick.append('0')
        if test_snare_Y[i] == 1:
            snare.append("F_sharp_3")
        else:
            snare.append('0')
        if test_hat_Y[i] == 1:
            hat.append("F_sharp_3")
        else:
            hat.append('0')
    return [piano, bass, kick, snare, hat]

pitches_list = np.array(convert_for_malmo(test_piano_Y, test_bass_Y, test_kick_Y, test_snare_Y, test_hat_Y))
pitches_list = np.reshape(pitches_list,(5,-1,32))

agent_start_pos_x = 0.5
agent_start_pos_y = 2
agent_start_pos_z = 0.5

def initNoteblocks(piano, bass, kick, snare, hat):
    # Create Row for sound 
    piano_tones_1 = piano.tolist()[:16]
    piano_tones_2 = piano.tolist()[-16:][::-1]

    bass_tones_1  = bass.tolist()[:16]
    bass_tones_2  = bass.tolist()[-16:][::-1]

    kick_tones_1  = kick.tolist()[:16]
    kick_tones_2  = kick.tolist()[-16:][::-1]
    
    snare_tones_1 = snare.tolist()[:16]
    snare_tones_2 = snare.tolist()[-16:][::-1]

    hat_tones_1   = hat.tolist()[:16]
    hat_tones_2   = hat.tolist()[-16:][::-1]

    # Reverse Second Half since it's going backwards  
    tone_row1 = [piano_tones_1, piano_tones_1, bass_tones_1, kick_tones_1, snare_tones_1, hat_tones_1]
    tone_row2 = [piano_tones_2, piano_tones_2, bass_tones_2, kick_tones_2, snare_tones_2, hat_tones_2]
    pitch_block = ["dirt", "dirt", "planks", "stone", "sand", "glass"]

    xml = ""
    # Draw the noteblocks:
    for i in range(1,17):
        for x in range(-2,4):
            if tone_row1[x+2][i-1] == '0':
                xml+= '''<DrawBlock x="{x}" y="2" z="{z}" type="stone"/>'''.format(x=x, z=(i*2)+1)
            else:
                xml += '''<DrawBlock x="{x}" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'''.format(x=x, z=(i*2)+1, pitch = tone_row1[x+2][i-1])
                xml += '''<DrawBlock x="{x}" y="1" z="{z}" type="{type}"/>'''.format(x=x, z=(i*2)+1,type=pitch_block[x+2])
            if tone_row2[x+2][i-1] == '0':
                xml+= '''<DrawBlock x="{x2}" y="2" z="{z}" type="stone"/>'''.format(x2=x+7, z=(i*2)+1)
            else:
                xml += '''<DrawBlock x="{x2}" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'''.format(x2=x+7, z=(i*2)+1, pitch = tone_row2[x+2][i-1])
                xml += '''<DrawBlock x="{x2}" y="1" z="{z}" type="{type}"/>'''.format(x2=x+7, z=(i*2)+1,type=pitch_block[x+2])

    for k in range(1,18):
        for x in range(-2,4):
            if k != 1:
                xml += '<DrawBlock x="{x2}" y="2" z="{z}" type="unpowered_repeater" face="SOUTH"/>'.format(x2=x+7, z=(k*2))
            if k != 17:
                xml += '<DrawBlock x="{x}" y="2" z="{z}" type="unpowered_repeater" face="NORTH"/>'.format(x=x, z=(k*2))
    xml += '<DrawBlock x="0" y="2" z="0" type="wooden_pressure_plate" />'
        

    xml += '''<DrawLine x1="-2" x2="3" y1="2" y2="2" z1="1" z2="1" type="redstone_wire"/>
            <DrawLine x1="3" x2="10" y1="2" y2="2" z1="35" z2="35" type="redstone_wire"/>
            <DrawLine x1="10" x2="17" y1="2" y2="2" z1="1" z2="1" type="redstone_wire"/>
            <DrawBlock x="3" y="2" z="34" type="redstone_wire"/>
            <DrawBlock x="10" y="2" z="2" type="redstone_wire"/>'''
    
    return xml

def addNoteblocks(currX, piano, bass, kick, snare, hat):
    # Create Row for sound
    piano_tones_1 = piano.tolist()[:16]
    piano_tones_2 = piano.tolist()[-16:][::-1]

    bass_tones_1  = bass.tolist()[:16]
    bass_tones_2  = bass.tolist()[-16:][::-1]

    kick_tones_1  = kick.tolist()[:16]
    kick_tones_2  = kick.tolist()[-16:][::-1]
    
    snare_tones_1 = snare.tolist()[:16]
    snare_tones_2 = snare.tolist()[-16:][::-1]

    hat_tones_1   = hat.tolist()[:16]
    hat_tones_2   = hat.tolist()[-16:][::-1]

    tone_row1 = [piano_tones_1, piano_tones_1, bass_tones_1, kick_tones_1, snare_tones_1, hat_tones_1]
    tone_row2 = [piano_tones_2, piano_tones_2, bass_tones_2, kick_tones_2, snare_tones_2, hat_tones_2]

    pitch_block = ["dirt", "dirt", "planks", "stone", "sand", "glass"]
    xml = ""
    # Draw the noteblocks:
    for i in range(1,17):
        for x in range(currX,currX+6):
            if tone_row1[x-currX][i-1] == '0': 
                xml+= '<DrawBlock x="{x}" y="2" z="{z}" type="stone"/>'.format(x=x,z=(i*2)+1)
            else:
                xml += '<DrawBlock x="{x}" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'.format(x=x, z=(i*2)+1, pitch = tone_row1[x-currX][i-1])
                xml += '<DrawBlock x="{x}" y="1" z="{z}" type="{type}"/>'.format(x=x, z=(i*2)+1, type=pitch_block[x-currX])
        
            if tone_row2[x-currX][i-1] == '0':
                xml += '<DrawBlock x="{x2}" y="2" z="{z}" type="stone"/>'.format(x2=x+7,z=(i*2)+1)
            else:
                xml += '<DrawBlock x="{x2}" y="2" z="{z}" type="noteblock" variant="{pitch}"/>'.format(x2=x+7, z=(i*2)+1, pitch = tone_row2[x-currX][i-1])
                xml += '<DrawBlock x="{x2}" y="1" z="{z}" type="{type}"/>'.format(x2=x+7,z=(i*2)+1,type=pitch_block[x-currX])

    for k in range(1,18):
        for x in range(currX, currX+6):
            if k != 1:
                xml += '<DrawBlock x="{x2}" y="2" z="{z}" type="unpowered_repeater" face="SOUTH"/>'.format(x2=x+7, z=(k*2))
            if k != 17:
                xml += '<DrawBlock x="{x}" y="2" z="{z}" type="unpowered_repeater" face="NORTH"/>'.format(x=x, z=(k*2))
        

    xml += '''<DrawLine x1="{x}" x2="{x1}" y1="2" y2="2" z1="1" z2="1" type="redstone_wire"/>
              <DrawLine x1="{x1}" x2="{x3}" y1="2" y2="2" z1="35" z2="35" type="redstone_wire"/>
              <DrawLine x1="{x2}" x2="{x3}" y1="2" y2="2" z1="1" z2="1" type="redstone_wire"/>
              <DrawBlock x="{x1}" y="2" z="34" type="redstone_wire"/>
              <DrawBlock x="{x2}" y="2" z="2" type="redstone_wire"/>'''.format(x=currX, x1=currX+5, x2=currX+7, x3=currX+14)

    return xml

def write_XML(pitches):
    xml = ""
    for i in range(len(pitches[0])):
        if i == 0:
            xml += initNoteblocks(pitches[0][i], pitches[1][i], pitches[2][i], pitches[3][i], pitches[4][i])
        else:
            xml += addNoteblocks(12+(15*(i-1)), pitches[0][i], pitches[1][i], pitches[2][i], pitches[3][i], pitches[4][i])
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
                <DrawingDecorator>''' + write_XML(pitches_list) + '''</DrawingDecorator>
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
max_retries = 10
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
# while world_state.is_mission_running:
#     print(".", end="")
#     agent_host.sendCommand("move 1")
#     time.sleep(0.05)
#     agent_host.sendCommand("move 0")
#     world_state = agent_host.getWorldState()
#     for error in world_state.errors:
#         print("Error:",error.text)

print()
print("Mission ended")
# Mission has ended.
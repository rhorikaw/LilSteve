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

sixteenth_note_value = 12.5  ### 60/ (4*BPM)

test_piano_Y = []
test_bass_Y = []
test_kick_Y = []
test_snare_Y = []
test_hat_Y = []

piano_data = open('piano.csv','r')
piano_data_reader = csv.reader(piano_data)
piano_mean = 0
piano_sd = 0
piano_n = 0
line_num = 0
for row in piano_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            piano_mean += col
            piano_n += 1
    line_num += 1
line_num = 0
piano_mean = piano_mean/piano_n
piano_data.close()

piano_data = open('piano.csv','r')
piano_data_reader = csv.reader(piano_data)
for row in piano_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            piano_sd += (col - piano_mean)*(col - piano_mean)
    line_num += 1
piano_sd = piano_sd/piano_n
piano_sd = math.sqrt(piano_sd)
two_piano_sd = piano_mean + 2*piano_sd
piano_data.close()

line_num = 0
note_index = 0
piano_data = open('piano.csv','r')
piano_data_reader = csv.reader(piano_data)
for row in piano_data_reader:
    row = [float(i) for i in row]
    if line_num >= 2 and (line_num-6) == round(sixteenth_note_value*note_index):
        if max(row) > two_piano_sd:
            test_piano_Y.append(1)
        else:
            test_piano_Y.append(0)
        note_index += 1
    line_num +=1
piano_data.close()

bass_data = open('bass.csv','r')
bass_data_reader = csv.reader(bass_data)
bass_mean = 0
bass_sd = 0
bass_n = 0
line_num = 0
for row in bass_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            bass_mean += col
            bass_n += 1
    line_num += 1
line_num = 0
bass_mean = bass_mean/bass_n
bass_data.close()

bass_data = open('bass.csv','r')
bass_data_reader = csv.reader(bass_data)
for row in bass_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            bass_sd += (col - bass_mean)*(col - bass_mean)
    line_num += 1
bass_sd = bass_sd/bass_n
bass_sd = math.sqrt(bass_sd)
two_bass_sd = bass_mean + 2*bass_sd
bass_data.close()

bass_data = open('bass.csv','r')
bass_data_reader = csv.reader(bass_data)
line_num = 0
note_index = 0
for row in bass_data_reader:
    row = [float(i) for i in row]
    if line_num >= 2 and (line_num-6) == round(sixteenth_note_value*note_index):
        if max(row) > two_piano_sd:
            test_bass_Y.append(1)
        else:
            test_bass_Y.append(0)
        note_index += 1
    line_num +=1
bass_data.close()

snare_data = open('snare.csv','r')
snare_data_reader = csv.reader(snare_data)
snare_mean = 0
snare_sd = 0
snare_n = 0
line_num = 0
for row in snare_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            snare_mean += col
            snare_n += 1
    line_num += 1
line_num = 0
snare_mean = snare_mean/snare_n
snare_data.close()

snare_data = open('snare.csv','r')
snare_data_reader = csv.reader(snare_data)
for row in snare_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            snare_sd += (col - snare_mean)*(col - snare_mean)
    line_num += 1
snare_sd = snare_sd/snare_n
snare_sd = math.sqrt(snare_sd)
two_snare_sd = snare_mean + 7*snare_sd
snare_data.close()

snare_data = open('snare.csv','r')
snare_data_reader = csv.reader(snare_data)
line_num = 0
note_index = 0
for row in snare_data_reader:
    row = [float(i) for i in row]
    if line_num >= 2 and (line_num-6) == round(sixteenth_note_value*note_index):
        if max(row) > two_snare_sd:
            test_snare_Y.append(1)
        else:
            test_snare_Y.append(0)
        note_index += 1
    line_num +=1
snare_data.close()

kick_data = open('kick.csv','r')
kick_data_reader = csv.reader(kick_data)
kick_mean = 0
kick_sd = 0
kick_n = 0
line_num = 0
for row in kick_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            kick_mean += col
            kick_n += 1
    line_num += 1
line_num = 0
kick_mean = kick_mean/kick_n
kick_data.close()

kick_data = open('kick.csv','r')
kick_data_reader = csv.reader(kick_data)
for row in kick_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            kick_sd += (col - kick_mean)*(col - kick_mean)
    line_num += 1
kick_sd = kick_sd/kick_n
kick_sd = math.sqrt(kick_sd)
two_kick_sd = kick_mean + 8*kick_sd
kick_data.close()

kick_data = open('kick.csv','r')
kick_data_reader = csv.reader(kick_data)
line_num = 0
note_index = 0
for row in kick_data_reader:
    row = [float(i) for i in row]
    if line_num >= 2 and (line_num-6) == round(sixteenth_note_value*note_index):
        if max(row) > two_kick_sd:
            test_kick_Y.append(1)
        else:
            test_kick_Y.append(0)
        note_index += 1
    line_num +=1
kick_data.close()

hihat_data = open('hihat.csv','r')
hihat_data_reader = csv.reader(hihat_data)
hihat_mean = 0
hihat_sd = 0
hihat_n = 0
line_num = 0
for row in hihat_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            hihat_mean += col
            hihat_n += 1
    line_num += 1
line_num = 0
hihat_mean = hihat_mean/hihat_n
hihat_data.close()

hihat_data = open('hihat.csv','r')
hihat_data_reader = csv.reader(hihat_data)
for row in hihat_data_reader:
    if line_num > 1:
        for col in row:
            col = float(col)
            hihat_sd += (col - hihat_mean)*(col - hihat_mean)
    line_num += 1
hihat_sd = hihat_sd/hihat_n
hihat_sd = math.sqrt(hihat_sd)
two_hihat_sd = hihat_mean + 6*hihat_sd
hihat_data.close()

hihat_data = open('hihat.csv','r')
hihat_data_reader = csv.reader(hihat_data)
line_num = 0
note_index = 0
for row in hihat_data_reader:
    row = [float(i) for i in row]
    if line_num >= 2 and (line_num-6) == round(sixteenth_note_value*note_index):
        if max(row) > two_hihat_sd:
            test_hat_Y.append(1)
        else:
            test_hat_Y.append(0)
        note_index += 1
    line_num +=1
hihat_data.close()


dfT = pd.read_excel("sna_Y.xlsx")
piano_YT = dfT.Piano.to_numpy()
bass_YT = dfT.Bass.to_numpy()
#kick_YT = dfT.Kick.to_numpy()
#snare_YT = dfT.Snare.to_numpy()
#hat_YT = dfT.Hat.to_numpy()

piano_acc = 1 - sum(np.absolute(test_piano_Y-piano_YT))/len(piano_YT)
bass_acc = 1 - sum(np.absolute(test_bass_Y-bass_YT))/len(bass_YT)
#kick_acc = 1 - sum(np.absolute(test_kick_Y-kick_YT))/len(kick_YT) 
#snare_acc = 1 - sum(np.absolute(test_snare_Y-snare_YT))/len(snare_YT) 
#hat_acc = 1 - sum(np.absolute(test_hat_Y-hat_YT))/len(hat_YT)
overall_acc = np.average([piano_acc, bass_acc])

print("Note Accuracies:\n\tPiano: {p_a}% \n\tBass: {b_a}% \n\tOverall: {o_a}%".format( 
    p_a = piano_acc*100,
    b_a = bass_acc*100, 
    o_a = overall_acc*100))


def convert_for_malmo(test_piano_Y, test_bass_Y, test_kick_Y, test_snare_Y, test_hat_Y ):
    piano, bass = get_pitches_from_XML('SevenNationArmy.xml')
    kick = []
    snare = []
    hat = []
    for i in range(len(test_piano_Y)):
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

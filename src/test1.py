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

# Tutorial sample #2: Run simple mission using raw XML

from builtins import range
import MalmoPython
import os
import sys
import time
pitches = [
        "F_sharp_3",
        "G3",
        "G_sharp_3",
        "A3",
        "A_sharp_3",
        "B3",
        "C4",
        "C_sharp_4",
        "D4",
        "D_sharp_4",
        "E4",
        "F4",
        "F_sharp_4",
        "G4",
        "G_sharp_4",
        "A4",
        "A_sharp_4",
        "B4",
        "C5",
        "C_sharp_5",
        "D5",
        "D_sharp_5",
        "E5",
        "F5",
        "F_sharp_5"]
if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)

# More interesting generator string: "3;7,44*49,73,35:1,159:4,95:13,35:13,159:11,95:10,159:14,159:6,35:6,95:6;12;"

import csv
c = open('Scales.csv','r')
o = csv.reader(c)
i = 0
frequencies = []
n = {}
for r in o:
    r = [float(i) for i in r]
    if i == 0:
        frequencies = r
    elif i >= 2 and (i-6) % 50 == 0:
        n[i] = frequencies[r.index(max(r))]
    i+=1
for k in n:
    n[k] = int(round(n[k]))
notes = {247:5,262:6,277:7,294:8,311:9,330:10,349:11,370:12,392:13,415:14,440:15,466:16,494:17,523:18}
#notes = {247:"B3",262:6,277:7,294:8,311:9,330:10,349:11,370:12,392:13,415:14,440:15,466:16,494:17,523:18}
circuit = ""
for i in range(len(n)*2):
    circuit += "<DrawBlock x='{}'  y='2' z='{}' type='stone' />".format(1, 1+i*2)
    circuit += "<DrawBlock x='{}'  y='2' z='{}' type='powered_repeater' />".format(1, 2+i*2)
notes1 = ""
for i in range(len(n)):
    notes1 += "<DrawBlock x='{}'  y='2' z='{}' type='noteblock' variant='{}' />".format(1, 3+i*4,pitches[notes[int(n[i*50+6])]])
missionXML='''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
                <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

                    <About>
                        <Summary>Diamond Collector</Summary>
                    </About>

                    <ServerSection>
                        <ServerInitialConditions>
                            <Time>
                                <StartTime>12000</StartTime>
                                <AllowPassageOfTime>false</AllowPassageOfTime>
                            </Time>
                            <Weather>clear</Weather>
                        </ServerInitialConditions>
                        <ServerHandlers>
                            <FlatWorldGenerator generatorString="3;7,2;1;"/>
                            <DrawingDecorator>''' + \
                                "<DrawCuboid x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='air'/>".format(-50, 50, -50, 50) + \
                                "<DrawCuboid x1='{}' x2='{}' y1='1' y2='1' z1='{}' z2='{}' type='grass'/>".format(-50, 50, -50, 50) + \
                                circuit + \
                                notes1 + \
                                '''<DrawBlock x='0'  y='2' z='0' type='air' />
                                <DrawBlock x='1'  y='2' z='0' type='lever' />
                                <DrawBlock x='1'  y='2' z='1' type='redstone_wire' />
                                <DrawBlock x='0'  y='2' z='1' type='wooden_pressure_plate' />
                            </DrawingDecorator>
                            <ServerQuitWhenAnyAgentFinishes/>
                        </ServerHandlers>
                    </ServerSection>

                    <AgentSection mode="Survival">
                        <Name>CS175DiamondCollector</Name>
                        <AgentStart>
                            <Placement x="0.5" y="2" z="0.5" pitch="45" yaw="0"/>
                            <Inventory>
                                <InventoryItem slot="0" type="diamond_pickaxe"/>
                            </Inventory>
                        </AgentStart>
                        <AgentHandlers>
                            <DiscreteMovementCommands/>
                            <ObservationFromFullStats/>
                            <ObservationFromRay/>
                            <ObservationFromGrid>
                                <Grid name="floorAll">
                                    <min x="-'''+str(int(4/2))+'''" y="-1" z="-'''+str(int(4/2))+'''"/>
                                    <max x="'''+str(int(4/2))+'''" y="0" z="'''+str(int(4/2))+'''"/>
                                </Grid>
                            </ObservationFromGrid>
                            <RewardForCollectingItem>
                                <Item reward="1.0" type="diamond"/>
                            </RewardForCollectingItem>
                            <RewardForTouchingBlockType>
                                <Block reward="-1.0" type="lava"/>
                            </RewardForTouchingBlockType>
                            <AgentQuitFromReachingCommandQuota total="'''+str(3*100)+'''" />
                            <AgentQuitFromTouchingBlockType>
                                <Block type="bedrock" />
                            </AgentQuitFromTouchingBlockType>
                        </AgentHandlers>
                    </AgentSection>
                </Mission>'''

# Create default Malmo objects:

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

my_mission = MalmoPython.MissionSpec(missionXML, True)
my_mission_record = MalmoPython.MissionRecordSpec()

# Attempt to start a mission:
max_retries = 3
for retry in range(max_retries):
    try:
        agent_host.startMission( my_mission, my_mission_record )
        break
    except RuntimeError as e:
        if retry == max_retries - 1:
            print("Error starting mission:",e)
            exit(1)
        else:
            time.sleep(2)

# Loop until mission starts:
print("Waiting for the mission to start ", end=' ')
world_state = agent_host.getWorldState()
while not world_state.has_mission_begun:
    print(".", end="")
    time.sleep(0.1)
    world_state = agent_host.getWorldState()
    for error in world_state.errors:
        print("Error:",error.text)

print()
print("Mission running ", end=' ')

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

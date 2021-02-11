---
layout: default
title: Status
---
## Summary of the Project
For this project, we wish to create a program that takes a song chosen by the user and constructs a Minecraft note block circuit that reproduces the song. The input to the system is an audio file which is less than five minutes. Our output is a Minecraft circuit complete with redstone, repeaters, and note blocks that when activated, produces the input audio in Minecraft. To make our output sound more like the input, we will also be using different Minecraft blocks underneath the note blocks, which changes the type of sound the note block produces by changing the instrument that is played. A possible application of our project is a song recognition app for a smartphone.

## Approach
![1](https://user-images.githubusercontent.com/28813330/107708419-4dad2400-6c78-11eb-8acc-c2a6fd013959.JPG)
![2](https://user-images.githubusercontent.com/28813330/107708507-76351e00-6c78-11eb-9590-dc8144d0cb64.JPG)
![5](https://user-images.githubusercontent.com/28813330/107708503-759c8780-6c78-11eb-9ead-f4636bb208b5.JPG) 
In this project, we first began by procesing our input so that we
wouild have the data available that we required for training.  Our
original input was an audio file that we generated using a desktop
instrument player that we were then able to convert  into a readable
csv file that could be used as input for our program. Each line of the
csv file corrresponds to the frequency of the audo recorded every one
hundreth of a second. From the csv file, we know which frequencies are
being heard at each specific moment in time and the amount of time
that the specific frequency is being played for. For example, in our
model, if there is a frequency that is being played for 50 lines in
our csv file, we know that this corresponds to a half second of time
in the input file. From this file, we then can determine how long each
note of the song is being played, and using each frequency value we
can map each note to a specific pitch that can be represented in
Minecraft.
![3](https://user-images.githubusercontent.com/28813330/107708509-76351e00-6c78-11eb-93e2-6c61336eef70.JPG)
![4](https://user-images.githubusercontent.com/28813330/107708501-7503f100-6c78-11eb-88f5-9208ce9af28c.JPG)
The machine learning model that we are using to approach our scenario
is a classifier specifically we are using a random forest algorithm in
order to classify our data. Once we have determined the basic notes
that are played, we use our main algorithm in to assign an instrument
to each note that best reproduces the sounds that we have gathered
from our input file. In Minecraft, the instrument that a note block
produces depends on the material that is below the noteblock. For
example, placing a noteblock on top of grass produces a piano sound.
Each note can then be represented by one of the five possible
instruments that can be heard in the game, (kick drum, snare drum,
high-hat, harp, or bass) chosen by our Random forest model. The module
that we are using is sklearn.ensemble.RandomForestClassifier.
## Evaluation

## Remaining Goals and Challenges

## Resources Used
For this project, we are using AnthemScore’s Neural Network system which takes an audio file and produces a csv file that contains the amplitudes of different frequencies at different time intervals. To parse through the csv file, we are using the python library’s csv module. We are also using the note_block_test file provided in Malmo’s Python_Examples as a guide to generate the note blocks in different pitches. We used Ableton to generate the initial sample songs. Finally, we are using the mltools library in order to train and utilize our random forest classifier.

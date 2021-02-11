---
layout: default
title: Status
---
## Summary of the Project
For this project, we wish to create a program that takes a song chosen by the user and constructs a Minecraft note block circuit that reproduces the song. The input to the system is an audio file which is less than five minutes. Our output is a Minecraft circuit complete with redstone, repeaters, and note blocks that when activated, produces the input audio in Minecraft. To make our output sound more like the input, we will also be using different Minecraft blocks underneath the note blocks, which changes the type of sound the note block produces by changing the instrument that is played. A possible application of our project is a song recognition app for a smartphone.

## Approach

## Evaluation

## Remaining Goals and Challenges

## Resources Used
For this project, we are using AnthemScore’s Neural Network system which takes an audio file and produces a csv file that contains the amplitudes of different frequencies at different time intervals. To parse through the csv file, we are using the python library’s csv module. We are also using the note_block_test file provided in Malmo’s Python_Examples as a guide to generate the note blocks in different pitches. We used Ableton to generate the initial sample songs. Finally, we are using the mltools library in order to train and utilize our random forest classifier.

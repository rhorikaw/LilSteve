---
layout: default
title: Proposal
---
## Summary of the Project
The main idea of this project is to take a song that is chosen by a user and then form a representation of that song in Minecraft using music note blocks and pressure plates. The input is an audio file of a song that falls within our time limits of around 5 minutes. Our output is the Minecraft stage that contains the music blocks and the agent that will activate them in the correct order corresponding to the inputted link. A possible application of our project is a song recognition app for a smartphone.

## AI/ML Algorithms
For our project, we plan on using recurrent neural networks in order to generate the music blocks that will create the desired audio in minecraft. Recently, recurrent neural networks have become immensely popular in the field of machine learning due to their effectiveness in modeling sequence-to-sequence learning. This means that recurrent neural networks are very useful in areas such as speech recognition, translation, and speech synthesis, which all have to do with audio generation. This is due to the fact that recurrent neural networks use sequential data, which allows them to exhibit temporal dynamic behavior in order to solve temporal problems. Therefore, we believe that the task of translating from music in the real world to note blocks in Minecraft would be best solved using recurrent neural networks.

## Evaluation Plan
Quantitative metrics are difficult to measure in a project like this, as there’s no clear-cut way to measure the similarity between two different audio files. The run-time of the output should ideally be the same duration as the inputted video. While observing the past projects that were similar to ours, we noticed that they did not explore the different types of sounds Minecraft note blocks can make. For example, a note block placed on a dirt block produces a piano sound, while a stone block produces a bass kick sound. Thus the current baseline is a random note block circuit that only uses piano sounds, but we hope to create a more orchestral Minecraft note block circuit that uses more than one instrument.\
\
We will show how the project works by showing the results of basic unit tests. These will mainly entail the conversion of a few scales with a varying number of instruments. Musical scales are very short and simple, and thus would serve well as the unit test. Our algorithm is responsible for generating a world with a bunch of noteblocks. Thus, the world that we build using XML will be our “visualizer” to help see what kind of world our song generator outputs. Our moonshot case would be an AI that can generate both a Minecraft world and an agent that can successfully interact with each other to create a cover of any Spotify or YouTube audio.

## Appointment with the Instructor
Our appointment will be on Wednesday, January 20 at 4:30 PM.

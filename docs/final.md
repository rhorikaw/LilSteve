---
layout: default
title: Final Report
---
## Final Video

## Summary of the Project
From its in-game soundtrack to jukeboxes and noteblocks, Minecraft’s music is an iconic component of the game’s history. A quick YouTube search demonstrates the popularity of Minecraft’s music with the top videos garnering hundreds of millions of views. Minecraft noteblock circuit videos are no exception to this phenomenon as millions of viewers show up to listen to the Minecraft rendition of their favorite song. In addition to the actual songs, tutorials about creating noteblock circuits that replicate various songs are also immensely prevalent, illustrating the demand for this type of content. However, while detailing the steps that are necessary to create noteblock circuits, these videos also note that the creation process often takes many hours to even days in order to complete. Therefore the construction of a product that enables users to enjoy their favorite songs within the beauty of Minecraft’s music without the exorbitant time sink is one that is not only practical but also fills a massive demand.\
\
The goal of our project is to take in a song as input and create a noteblock representation of that song in Minecraft. The input is any audio file chosen by the user. The Minecraft representation of the song consists of a series of note blocks connected into a redstone circuit that plays the completed song when powered. The type of Minecraft block that is placed underneath each note block determines the sound that the note block creates. In order to make our representation of the input song sound as close as possible to the original, we are using machine learning algorithms to choose the correct type of block to place under each note.\
\
<img src="https://user-images.githubusercontent.com/36008213/111890732-8f349b80-89a9-11eb-8fa1-e9bd7006add4.png" width="70%" height="70%">\
(Minecraft Circuit Program Output)\
\
Our project is essentially split into two parts, both of which are certainly not trivial, and required a lot of work to complete. The first challenge we had to solve was figuring out when each note was being played and which note was being played at that particular time. In order to do this, we used Neural Networks, and this mapping from time to notes was necessary and used for each of the models that handled the second aspect of this project. The second piece that we needed to work out was determining which instrument was being played at which time. To do this, we used Random Forests and Neural Networks, and we placed the corresponding block below note blocks to create the desired sound. Both of these tasks required machine learning because they involved the recognition of various patterns and sound in order to recognize the start of notes and the sound of instruments.

## Approaches
### Note Type and Timing
One of the first tasks that we had to accomplish was to be able to detect when each note of a song was being played. The first way that was attempted to do this was by looking at the xml representation of the song produced by anthem score. The approach that was taken when analyzing the csv file representation of the song from Anthemscore was to extract the maximum amplitude that was recorded at each millisecond of the audio file. This data could then be visualized as a graph of amplitude over time. In this approach, the local maxima in the graph would be the time that a note was played, and the frequency corresponding to the column in the csv file would be the frequency of the note that was played. This approach in identifying specific notes of a song produced an audio representation that was unrecognizable as the original song, so we had to take a different approach using the xml file.

![1](https://raw.githubusercontent.com/rhorikaw/LilSteve/main/docs/Figure_1.png)

To generate data for this project, we sent in an audio file into AnthemScore, which is a software that uses neural networks to generate spectrograms, sheet music, and other interesting types of data. We mainly focused on the spectrograms and the xml files in our project to give us a better understanding of what kind of sounds are occurring at what point in the audio file. After retrieving the spectrogram data, we parsed the data so that we only have data for the intervals we are interested in. We did this by using a simple formula:
    Seconds per 16th note = 15 / BPM 
The value we get from this formula will indicate how many rows we would need to skip by, since each row of the csv file indicates a hundredth of a second. 

<img src="https://user-images.githubusercontent.com/36008213/111897628-4cd98180-89de-11eb-8714-703c6b35788e.png" width="70%" height="70%">

### Random Forest Classifier
One approach we tried was to send the values of the csv file into multiple Random Forest Classifiers to train the classifier on when an instrument is being played. To do this, we first generated test audio data from a Digital Audio Workstation (DAW) called Ableton. Then, we send it to AnthemScore to generate the csv file, and parse it as mentioned before. Then we created an excel sheet that indicates when each instrument was being played on 16th note intervals for all of the samples. Then we use this data with the data from the csv file to train a Random Forest Classifier for each instrument sound that is in Minecraft. Lastly, we passed in the test audio file, which was the song “Seven Nation Army” from the band The White Stripes, into AnthemScore to get our “x” values to predict from.

### Neural Networks
The idea behind the Neural Network model was to split the song into the five instruments that Minecraft supports, and then figure out which ones were playing at which times. In terms of splitting the song up, the goal was to have the original song as input, and to output five files, each containing only one instrument. The aim was to have each file have the instrument playing at the time it is playing during the original song, and to have the audio file be silent when that instrument is not playing. Then once we have all of the instrument files, we can take our AnthemScore mapping of notes being played at specific times, and use the split up song to see which instrument is playing which notes. To do this, we first run each of the five files through AnthemScore to get a csv file for each instrument containing the amplitude of every frequency for every 0.1 second interval. After we get the csv files, we can look at each time point where a note is being played, given by the Note Type and Timing section above, and if the amplitude of an instrument at that time point is above a certain threshold, we can say that the instrument is being played, at the pitch also given by the Note Type and Timing section above. Then, based on the instrument that is playing, we can place a block underneath the note block in order to create the desired sound.\
\
<img src="https://user-images.githubusercontent.com/36008213/111913244-7cae7680-8a2a-11eb-8135-7b6962645f50.png" width="70%" height="70%">\
(NN Model training)\
\
The reason this is called the Neural Network model is because we used Neural Networks to split the song into the five different instrument files. To do this, we first created twenty different songs using Ableton in order to allow the model to train. Each of the songs had six components: a snare, kick, hi-hat, bass, piano, and mix. The snare, kick, hi-hat, bass, and piano each had their own separate files for each of the twenty songs, and the mix contained all of the instruments together for each song. Then, to split the song up into separate tracks, we input the twenty sample songs into our Neural Network model with a learning rate of 0.0001 and a maximum number of training steps for each song of 1000. Then meant that with each song that was added, the amount of training that would be done scaled up considerably. We used ELU as our activation function, which has the equation :\
\
<img src="https://render.githubusercontent.com/render/math?math={f(x) = x%20|%20x >= 0}">\
<img src="https://render.githubusercontent.com/render/math?math={f(x) = \alpha(e^x-1)%20|%20x < 0}">\
\
The derivative of this equation is fed into the backpropagation algorithm during learning. This is:\
\
<img src="https://render.githubusercontent.com/render/math?math={f'(x) = 1%20|%20x >= 0}">\
<img src="https://render.githubusercontent.com/render/math?math={f'(x) = \alpha e^x%20|%20x < 0}">\
\
After training, we pass the user’s input song into our model, and we get the split instrument files as our output which we can then pass to AnthemScore as described above.


### Advantages and Disadvantages


## Evaluation
### Random Forest Classifier
#### Quantitative Analysis
 Again, getting a spot-on quantitative evaluation of our project is a tough task. Since we are limited with what kind of instrument, tempo, and meter we can use, we are limited with what we can evaluate as well. Since we used the YouTube video, it’s impossible to tell exactly when each instrument is being played, but we can get a good estimate with a little bit of music knowledge. We created an excel sheet for the expected values for each instrument, and compared them with the output of the Random Forest Classifiers to get an estimate of the accuracy of our models. We were able to achieve an overall accuracy of 91%, but despite its accuracy, the song was still unrecognizable in some parts. However, although it was not a perfect model, we believe that the performance could be improved by using more test data. 

#### Qualitative Analysis
On the qualitative aspect, the song generated by the model is recognizable, at best. Initially, we attempted to decipher which notes were being played by inspecting the spectrogram generated by AnthemScore, but after adding multiple instruments into the picture this became more difficult to do, and the songs on Minecraft became more and more unrecognizable. For this reason, we proceeded to rely on AnthemScore’s xml file, which had more accurate predictions of the pitches of the notes. The famous bass line of the song is audible, but the subtler vocals are more scattered and less accurate. However we believe that with more training data, the performance of the classifier could be boosted even more.

### Neural Networks
#### Quantitative Analysis

#### Qualitative Analysis

### Comparison
#### Quantitative Analysis

#### Qualitative Analysis

## References
https://minecraft.gamepedia.com/Note_Block

https://www.lunaverus.com/

https://www.ableton.com/


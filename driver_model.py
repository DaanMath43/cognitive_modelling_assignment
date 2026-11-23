### 
### This code is developed by Christian P. Janssen of Utrecht University
### It is intended for students from the Master's course Cognitive Modeling
### Large parts are based on the following research papers:
### Janssen, C. P., & Brumby, D. P. (2010). Strategic adaptation to performance objectives in a dual‐task setting. Cognitive science, 34(8), 1548-1560. https://onlinelibrary.wiley.com/doi/full/10.1111/j.1551-6709.2010.01124.x
### Janssen, C. P., Brumby, D. P., & Garnett, R. (2012). Natural break points: The influence of priorities and cognitive and motor cues on dual-task interleaving. Journal of Cognitive Engineering and Decision Making, 6(1), 5-29. https://journals.sagepub.com/doi/abs/10.1177/1555343411432339
###
### If you want to use this code for anything outside of its intended purposes (training of AI students at Utrecht University), please contact the author:
### c.p.janssen@uu.nl



### 
### import packages
###
import matplotlib.pyplot as plt
import numpy
from itertools import product
import matplotlib.pyplot as plt
import numpy
from itertools import product
import math
import random



###
###
### Global parameters. These can be called within functions to change (Python: make sure to call GLOBAL)
###
###


###
### Car / driving related parameters
###
steeringUpdateTime = 250    #in ms ## How long does one steering update take? (250 ms consistent with Salvucci 2005 Cognitive Science)
timeStepPerDriftUpdate = 50 ### msec: what is the time interval between two updates of lateral position?
startingPositionInLane = 0.27 			#assume that car starts already slightly away from lane centre (in meters) (cf. Janssen & Brumby, 2010)


#parameters for deviations in car drift due the simulator environment: See Janssen & Brumby (2010) page 1555
gaussDeviateMean = 0
gaussDeviateSD = 0.13 ##in meter/sec



### The car is controlled using a steering wheel that has a maximum angle. Therefore, there is also a maximum to the lateral velocity coming from a steering update
maxLateralVelocity = 1.7	# in m/s: maximum lateral velocity: what is the maximum that you can steer?
minLateralVelocity = -1* maxLateralVelocity

startvelocity = 0 	#a global parameter used to store the lateral velocity of the car


###
### Switch related parameters
###
retrievalTimeWord = 200   #ms. ## How long does it take to think of the next word when interleaving after a word (time not spent driving, but drifting)
retrievalTimeSentence = 300 #ms. ## how long does it take to retrieve a sentence from memory (time not spent driving, but drifting)



###
### parameters for typing task
###
timePerWord = 0  ### ms ## How much time does one word take
wordsPerMinuteMean = 39.33   # parameters that control typing speed: when typing two fingers, on average you type this many words per minute. From Jiang et al. (2020; CHI)
wordsPerMinuteSD = 10.3 ## this si standard deviation (Jiang et al, 2020)


## Function to reset all parameters. Call this function at the start of each simulated trial. Make sure to reset GLOBAL parameters.
def resetParameters():
    global timePerWord
    global retrievalTimeWord
    global retrievalTimeSentence 
    global steeringUpdateTime 
    global startingPositionInLane 
    global gaussDeviateMean
    global gaussDeviateSD 
    global gaussDriveNoiseMean 
    global gaussDriveNoiseSD 
    global timeStepPerDriftUpdate 
    global maxLateralVelocity 
    global minLateralVelocity 
    global startvelocity
    global wordsPerMinuteMean
    global wordsPerMinuteSD
    
    timePerWord = 0  ### ms

    retrievalTimeWord = 200   #ms
    retrievalTimeSentence = 300 #ms
	
    steeringUpdateTime = 250    #in ms
    startingPositionInLane = 0.27 			#assume that car starts already away from lane centre (in meters)
	

    gaussDeviateMean = 0
    gaussDeviateSD = 0.13 ##in meter/sec
    gaussDriveNoiseMean = 0
    gaussDriveNoiseSD = 0.1	#in meter/sec
    timeStepPerDriftUpdate = 50 ### msec: what is the time interval between two updates of lateral position?
    maxLateralVelocity = 1.7	# in m/s: maximum lateral velocity: what is the maximum that you can steer?
    minLateralVelocity = -1* maxLateralVelocity
    startvelocity = 0 	#a global parameter used to store the lateral velocity of the car
    wordsPerMinuteMean = 39.33
    wordsPerMinuteSD = 10.3


##calculates if the car is not accelerating (m/s) more than it should (maxLateralVelocity) or less than it should (minLateralVelocity)  (done for a vector of numbers)
def velocityCheckForVectors(velocityVectors):
    global maxLateralVelocity
    global minLateralVelocity

    velocityVectorsLoc = velocityVectors

    if (type(velocityVectorsLoc) is list):
            ### this can be done faster with for example numpy functions
        velocityVectorsLoc = velocityVectors
        for i in range(len(velocityVectorsLoc)):
            if(velocityVectorsLoc[i]>1.7):
                velocityVectorsLoc[i] = 1.7
            elif (velocityVectorsLoc[i] < -1.7):
                velocityVectorsLoc[i] = -1.7
    else:
        if(velocityVectorsLoc > 1.7):
            velocityVectorsLoc = 1.7
        elif (velocityVectorsLoc < -1.7):
            velocityVectorsLoc = -1.7

    return velocityVectorsLoc  ### in m/s
	

## Function to determine lateral velocity (controlled with steering wheel) based on where car is currently positioned. See Janssen & Brumby (2010) for more detailed explanation.
## Lateral velocity update depends on current position in lane. Intuition behind function: the further away you are, the stronger the correction will be that a human makes
def vehicleUpdateActiveSteering(LD):

	latVel = 0.2617 * LD*LD + 0.0233 * LD - 0.022
	returnValue = velocityCheckForVectors(latVel)
	return returnValue ### in m/s
	

### function to update lateral deviation in cases where the driver is NOT steering actively (when they are distracted by typing for example). Draw a value from a random distribution. This can be added to the position where the car is already.
def vehicleUpdateNotSteering():
    
    global gaussDeviateMean
    global gaussDeviateSD 

    vals = numpy.random.normal(loc=gaussDeviateMean, scale=gaussDeviateSD,size=1)[0]
    returnValue = velocityCheckForVectors(vals)
    return returnValue   ### in m/s
    

###
### Section 2: e-mailing while driving
###
## Overview for readers:
##  - drift():     the driver is typing, so the car is NOT steered and drifts randomly (red points)
##  - steer():     the driver looks at the road and steers back towards lane centre (blue points)
##  - runTrial():  simulates one e-mail (nrSentences x nrWordsPerSentence) for one interleaving strategy
##  - plotTrial(): plots lane position over time for one trial
## Units: time in ms, lane position in m, velocities in m/s.
## Every 50 ms (timeStepPerDriftUpdate) one lane position is stored in locPos, plus its colour in locColor.


## Drift while NOT steering (e.g. while typing).
## For `duration` ms, update the position every 50 ms with a random lateral velocity.
## Velocity is in m/s, so multiply by (dt / 1000) to get the distance moved in one 50 ms step.
def drift(pos, duration, locPos, locColor):
    """Car drifts (no steering) for `duration` ms, one update per 50 ms."""
    dt = timeStepPerDriftUpdate
    for i in range(math.floor(duration / dt)):          ## rounded down to whole 50 ms steps
        pos = pos + vehicleUpdateNotSteering() * (dt / 1000)
        locPos.append(pos)
        locColor.append("red")                          ## red = no active steering
    return pos


## Active steering (driver attention on the road).
## Each steering movement takes 250 ms (steeringUpdateTime). The lateral velocity is computed ONCE
## per movement, based on the current distance from lane centre, and then applied in 5 steps of 50 ms.
## vehicleUpdateActiveSteering() assumes a positive lane deviation, so we pass abs(pos) and decide
## the direction ourselves: right of centre (pos > 0) -> move left, left of centre -> move right.
## NB: the formula is negative below ~0.25 m, so close to centre the car is pushed slightly outwards;
## the model therefore settles around ~0.25 m instead of exactly 0. This is a property of the model.
def steer(pos, nrMovements, locPos, locColor):
    """Active steering: nrMovements x 250 ms, position stored every 50 ms.
    Returns the new position and the time spent steering."""
    dt = timeStepPerDriftUpdate
    for k in range(nrMovements):
        latVel = vehicleUpdateActiveSteering(abs(pos))   # once per 250 ms
        for i in range(math.floor(steeringUpdateTime / dt)):   ## 250 / 50 = 5 position updates
            if pos > 0:
                pos = pos - latVel * (dt / 1000)
            else:
                pos = pos + latVel * (dt / 1000)
            locPos.append(pos)
            locColor.append("blue")                     ## blue = active steering
    return pos, nrMovements * steeringUpdateTime        ## also return the time spent steering (ms)


## Simulate one trial (= typing one e-mail while driving).
## Parameters:
##   nrWordsPerSentence, nrSentences:  size of the e-mail
##   nrSteeringMovementsWhenSteering:  how many 250 ms steering movements per driving break
##   interleaving:                     strategy: "word" (steer after every word) or "sentence" (after every sentence)
## Returns: total trial time (ms), list of lane positions (m), list of colours per position.
def runTrial(nrWordsPerSentence=5, nrSentences=3, nrSteeringMovementsWhenSteering=2, interleaving="word"):
    ## Step 1-2: reset the global parameters and create the storage variables
    resetParameters()
    locPos = []        ## all lane positions of this trial (one per 50 ms)
    locColor = []      ## colour per position: "red" = drifting, "blue" = steering
    trialTime = 0      ## running total of the trial time in ms
    ## Step 4: the car starts slightly away from lane centre (0.27 m)
    pos = startingPositionInLane

    ## Step 6: typing speed for THIS trial, sampled once from a normal distribution (Jiang et al., 2020).
    # typing speed: drawn once per trial, shared by all strategies
    wpm = numpy.random.normal(wordsPerMinuteMean, wordsPerMinuteSD)
    wpm = max(wpm, 1)                  ## guard: a draw <= 0 would give an impossible time per word
    timePerWord = 60000 / wpm          ## words per minute -> ms per word (1 minute = 60000 ms)

    ## Strategy "word": type one word, then steer, then the next word, etc.
    if interleaving == "word":
        ## Step 7: loop over sentences, and within each sentence over words
        for s in range(nrSentences):
            for w in range(nrWordsPerSentence):
                ## Step 8: time for this word = typing + retrieving the word ("where was I?")
                wordTime = timePerWord + retrievalTimeWord
                if w == 0:                                    ## first word of a sentence: also retrieve the sentence
                    wordTime += retrievalTimeSentence
                trialTime += wordTime
                ## Step 9: while typing the car drifts
                pos = drift(pos, wordTime, locPos, locColor)

                ## Step 10: steer after every word, except after the very last word of the e-mail
                lastWord = (s == nrSentences - 1) and (w == nrWordsPerSentence - 1)
                if not lastWord:
                    pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                    trialTime += steerTime

    ## Strategy "sentence": type a whole sentence, then steer.
    elif interleaving == "sentence":
        for s in range(nrSentences):
            # whole sentence in one go: sentence retrieval + all words, no per-word retrieval
            sentenceTime = retrievalTimeSentence + nrWordsPerSentence * timePerWord
            trialTime += sentenceTime
            pos = drift(pos, sentenceTime, locPos, locColor)  ## car drifts during the whole sentence

            if s < nrSentences - 1:          # no steering after the last sentence
                pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                trialTime += steerTime

    ## Strategy "drivingOnly" no typing, only steering for as long as typing WOULD have taken
    elif interleaving == "drivingOnly":
        # time the e-mail would have taken is (sentence retrieval + all words) per sentence, x number of sentences
        emailTime = (retrievalTimeSentence + nrWordsPerSentence * timePerWord) * nrSentences

        # steer() wants a NUMBER of 250 ms movements, not a time -> convert and round down to a whole number
        nrMovements = math.floor(emailTime / steeringUpdateTime)

        pos, steerTime = steer(pos, nrMovements, locPos, locColor)
        trialTime += steerTime

    elif interleaving == "none":
        emailTime = (retrievalTimeSentence + nrWordsPerSentence * timePerWord) * nrSentences

        pos = drift(pos, emailTime, locPos, locColor)  ## car drifts during the whole sentence
        trialTime += emailTime
    
    elif interleaving == "after_random_words":
        chunk_sizes = [2,3,4]

        for s in range(nrSentences):
            i = 0
            while i < nrWordsPerSentence:
                chunk_chosen = random.choice(chunk_sizes)
                words_left = nrWordsPerSentence - i
                if words_left < chunk_chosen:
                    chunk_chosen = words_left
                ## typing the chunk: every word costs timePerWord, but the word retrieval ("where was I?")
                ## is a switch cost, so it is paid once per chunk (after returning from the road), not per word
                wordTime = timePerWord * chunk_chosen + retrievalTimeWord
                if i == 0:                                    ## first chunk of a sentence: also retrieve the sentence
                    wordTime += retrievalTimeSentence
                trialTime += wordTime
                pos = drift(pos, wordTime, locPos, locColor)

                i += chunk_chosen                             ## move on, otherwise the while-loop never ends

                ## steer after every chunk, except after the very last chunk of the e-mail
                lastChunk = (s == nrSentences - 1) and (i >= nrWordsPerSentence)
                if not lastChunk:
                    pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                    trialTime += steerTime


    meanPos = numpy.mean(numpy.abs(locPos))   ## average distance from lane centre (absolute, so left/right don't cancel)
    maxPos = numpy.max(numpy.abs(locPos))     ## furthest from lane centre, regardless of side
    return trialTime,meanPos,maxPos


## Step 13: scatter plot of lane position over time for one trial.
## x-axis: each stored position is one 50 ms step, so step i is at i * 50 ms.
def plotTrial(trialTime, locPos, locColor):
    times = [i * timeStepPerDriftUpdate for i in range(len(locPos))]

    meanPos = numpy.mean(numpy.abs(locPos))   ## average distance from lane centre (absolute, so left/right don't cancel)
    maxPos = numpy.max(numpy.abs(locPos))     ## furthest from lane centre, regardless of side

    plt.scatter(times, locPos, c=locColor, s=8)   ## each point gets its own colour from locColor
    plt.xlabel("Time (ms)")
    plt.ylabel("Lane position (m)")
    plt.title(f"Total trial time = {trialTime:.0f} ms; "
              f"Mean position on the road = {meanPos:.3f} m; "
              f"Max position on the road (absolute) = {maxPos:.3f} m", fontsize=8)
    plt.show()

### function to run multiple simulations. Needs to be defined by students (section 3 of assignment)
def runSimulations(nrSims = 100):
    totalTime = []
    meanDeviation = []
    maxDeviation = []
    Condition = []
    amountOfWords=[15,16,17,18,19,20]

    for strategies in ["none","drivingOnly","sentence","word","after_random_words"]:
        print(strategies)
        for round in range(nrSims):
            wordsInSentence= (random.choice(amountOfWords))
            trialTime, meanPos, maxPos = runTrial(wordsInSentence, 10, 4, strategies)
            totalTime.append(trialTime)
            meanDeviation.append(meanPos)
            maxDeviation.append(maxPos)
            Condition.append(strategies)

    ## The plot with max deviation (y) against total trial time (x)
    ## every symbl represents a strategy, individual trials in grey, the mean per strategy in colour with SD error bars
    markers = {"none": "o", "drivingOnly": "^", "sentence": "s", "word": "x", "after_random_words": "D"}
    colors = {"none": "red", "drivingOnly": "blue", "sentence": "green", "word": "black", "after_random_words": "purple"}

    for strategy in markers:
        ## collect the trials that belong to this strategy
        times = []
        devs = []
        for i in range(len(Condition)):
            if Condition[i] == strategy:
                times.append(totalTime[i])
                devs.append(maxDeviation[i])

        ## individual trials are grey
        plt.scatter(times, devs, color="grey", marker=markers[strategy], s=15)
        ## The mean of this strategy bigger, in colour, with standard deviation as error bars
        plt.errorbar(numpy.mean(times), numpy.mean(devs),
                     xerr=numpy.std(times), yerr=numpy.std(devs),
                     color=colors[strategy], marker=markers[strategy], markersize=10,
                     capsize=4, label=strategy)

    plt.xlabel("Total trial time (ms)")
    plt.ylabel("Max lateral deviation (m)")
    plt.legend()
    plt.show()


## Section 4 (bonus A): implemented as interleaving="after_random_words" inside runTrial()


## Change the strategy here "word" or "sentence".
if __name__ == "__main__":
    #trialTime, locPos, locColor = runTrial(interleaving="drivingOnly")
    #plotTrial(trialTime, locPos, locColor)
    runSimulations()




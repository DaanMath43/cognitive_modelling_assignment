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
### Section 2, e-mailing while driving
###
## Quick overview of our part, with the Engineering parts of the assignment marked in the code below
## drift() is the car drifting while the driver is typing, so nobody is steering (red points)
## steer() is the driver looking at the road and steering back to the middle of the lane (blue points)
## runTrial() simulates typing one e-mail with one of the interleaving strategies
## plotTrial() plots the lane position over time for one trial
## Time is in ms, lane position in m and velocity in m/s
## Every 50 ms we store the lane position in locPos and its colour in locColor


## Engineering 2C1, drifting while not steering
## The car drifts while nobody is steering, for example while typing
## Every 50 ms the car gets a random sideways velocity for `duration` ms in total
## Velocity is in m/s, so we multiply by dt / 1000 to get how far the car moves in one 50 ms step
def drift(pos, duration, locPos, locColor):
    dt = timeStepPerDriftUpdate
    for i in range(math.floor(duration / dt)):          ## round down to whole 50 ms steps
        pos = pos + vehicleUpdateNotSteering() * (dt / 1000)
        locPos.append(pos)
        locColor.append("red")                          ## red means not steering
    return pos


## Engineering 2C1, active steering
## The driver looks at the road and steers
## One steering movement takes 250 ms. We work out the sideways speed once per movement,
## based on how far the car is from the middle, and then apply it in 5 small steps of 50 ms
## vehicleUpdateActiveSteering() expects a positive distance, so we give it abs(pos) and pick the direction ourselves
## If the car is right of the middle (pos > 0) we steer left, otherwise we steer right
## Note that the formula goes negative below about 0.25 m, so close to the middle the car gets pushed out a little
## That's why the car ends up hovering around 0.25 m instead of exactly 0, which is just how the model works
def steer(pos, nrMovements, locPos, locColor):
    dt = timeStepPerDriftUpdate
    for k in range(nrMovements):
        latVel = vehicleUpdateActiveSteering(abs(pos))   ## once every 250 ms
        for i in range(math.floor(steeringUpdateTime / dt)):   ## 250 / 50 gives 5 position updates
            if pos > 0:
                pos = pos - latVel * (dt / 1000)
            else:
                pos = pos + latVel * (dt / 1000)
            locPos.append(pos)
            locColor.append("blue")                     ## blue means steering
    return pos, nrMovements * steeringUpdateTime        ## we also return how long the steering took in ms


## Simulates one trial, which means typing one e-mail while driving
## nrWordsPerSentence and nrSentences set how long the e-mail is
## nrSteeringMovementsWhenSteering is how many 250 ms steering movements the driver makes per break
## interleaving is the strategy, so "word", "sentence", "drivingOnly", "none" or "after_random_words"
## It returns the total trial time in ms, the average distance from the middle of the lane and the max distance
def runTrial(nrWordsPerSentence=5, nrSentences=3, nrSteeringMovementsWhenSteering=2, interleaving="word"):
    ## reset the parameters and make the lists we store everything in
    resetParameters()
    locPos = []        ## every lane position of this trial, one every 50 ms
    locColor = []      ## colour for each position, red for drifting and blue for steering
    trialTime = 0      ## keeps track of the total trial time in ms
    ## the car starts a bit away from the middle of the lane (0.27 m)
    pos = startingPositionInLane

    ## pick a typing speed for this trial (Jiang et al., 2020)
    ## It's drawn once per trial and every strategy uses it the same way
    wpm = numpy.random.normal(wordsPerMinuteMean, wordsPerMinuteSD)
    wpm = max(wpm, 1)                  ## just in case we draw 0 or lower, which would make no sense
    timePerWord = 60000 / wpm          ## turn words per minute into ms per word (a minute is 60000 ms)

    ## Engineering 2C1, strategy "word", type one word, steer, type the next word and so on
    if interleaving == "word":
        ## go through every sentence and every word in it
        for s in range(nrSentences):
            for w in range(nrWordsPerSentence):
                ## a word takes the typing time plus the time to remember the next word
                wordTime = timePerWord + retrievalTimeWord
                if w == 0:                                    ## the first word of a sentence also needs the sentence to be remembered
                    wordTime += retrievalTimeSentence
                trialTime += wordTime
                ## the car drifts while we type
                pos = drift(pos, wordTime, locPos, locColor)

                ## steer after every word, but not after the very last word of the e-mail
                lastWord = (s == nrSentences - 1) and (w == nrWordsPerSentence - 1)
                if not lastWord:
                    pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                    trialTime += steerTime

    ## Engineering 2C2, strategy "sentence", type a whole sentence and then steer
    elif interleaving == "sentence":
        for s in range(nrSentences):
            ## the whole sentence in one go, so we remember the sentence once and pay nothing extra per word
            sentenceTime = retrievalTimeSentence + nrWordsPerSentence * timePerWord
            trialTime += sentenceTime
            pos = drift(pos, sentenceTime, locPos, locColor)  ## the car drifts during the whole sentence

            if s < nrSentences - 1:          ## no steering after the last sentence
                pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                trialTime += steerTime

    ## Engineering 3A, baseline "drivingOnly", no typing at all, just steering for as long as typing the e-mail would have taken
    elif interleaving == "drivingOnly":
        ## this is how long the e-mail would have taken to type
        emailTime = (retrievalTimeSentence + nrWordsPerSentence * timePerWord) * nrSentences

        ## steer() wants a number of 250 ms movements and not a time, so we convert it and round down
        nrMovements = math.floor(emailTime / steeringUpdateTime)

        pos, steerTime = steer(pos, nrMovements, locPos, locColor)
        trialTime += steerTime

    ## Engineering 3A, baseline "none", type the whole e-mail without ever looking at the road
    elif interleaving == "none":
        emailTime = (retrievalTimeSentence + nrWordsPerSentence * timePerWord) * nrSentences

        pos = drift(pos, emailTime, locPos, locColor)  ## the car drifts during the whole e-mail
        trialTime += emailTime

    ## Section 4 bonus A, strategy "after_random_words", steer after a random number of words (2, 3 or 4)
    elif interleaving == "after_random_words":
        chunk_sizes = [2,3,4]

        for s in range(nrSentences):
            i = 0
            while i < nrWordsPerSentence:
                chunk_chosen = random.choice(chunk_sizes)
                words_left = nrWordsPerSentence - i
                if words_left < chunk_chosen:
                    chunk_chosen = words_left
                ## every word in the chunk costs typing time, but remembering where you were only happens once per chunk
                ## because you only have to do that when you come back from steering
                wordTime = timePerWord * chunk_chosen + retrievalTimeWord
                if i == 0:                                    ## the first chunk of a sentence also needs the sentence to be remembered
                    wordTime += retrievalTimeSentence
                trialTime += wordTime
                pos = drift(pos, wordTime, locPos, locColor)

                i += chunk_chosen                             ## move on, otherwise the while loop never stops

                ## steer after every chunk, but not after the very last one of the e-mail
                lastChunk = (s == nrSentences - 1) and (i >= nrWordsPerSentence)
                if not lastChunk:
                    pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                    trialTime += steerTime


    ## Engineering 3B1, return trial time, mean and max deviation instead of plotting every position
    meanPos = numpy.mean(numpy.abs(locPos))   ## average distance from the middle of the lane, we use abs so left and right don't cancel out
    maxPos = numpy.max(numpy.abs(locPos))     ## the furthest the car got from the middle, no matter which side
    return trialTime,meanPos,maxPos


## Engineering 2C1, plot the lane position over time for one trial
## Each stored position is one 50 ms step, so position i happens at i * 50 ms
def plotTrial(trialTime, locPos, locColor):
    times = [i * timeStepPerDriftUpdate for i in range(len(locPos))]

    meanPos = numpy.mean(numpy.abs(locPos))   ## average distance from the middle of the lane, we use abs so left and right don't cancel out
    maxPos = numpy.max(numpy.abs(locPos))     ## the furthest the car got from the middle, no matter which side

    plt.scatter(times, locPos, c=locColor, s=8)   ## every point gets its own colour from locColor
    plt.xlabel("Time (ms)")
    plt.ylabel("Lane position (m)")
    plt.title(f"Total trial time = {trialTime:.0f} ms; "
              f"Mean position on the road = {meanPos:.3f} m; "
              f"Max position on the road (absolute) = {maxPos:.3f} m", fontsize=8)
    plt.show()

## Engineering 3B2, run all simulations and make the summary plot
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

    ## Plot the max deviation against the total trial time
    ## Every strategy gets its own symbol, single trials are grey and the mean per strategy is in colour with the SD as error bars
    markers = {"none": "o", "drivingOnly": "^", "sentence": "s", "word": "x", "after_random_words": "D"}
    colors = {"none": "red", "drivingOnly": "blue", "sentence": "green", "word": "black", "after_random_words": "purple"}

    for strategy in markers:
        ## grab the trials that belong to this strategy
        times = []
        devs = []
        for i in range(len(Condition)):
            if Condition[i] == strategy:
                times.append(totalTime[i])
                devs.append(maxDeviation[i])

        ## single trials in grey
        plt.scatter(times, devs, color="grey", marker=markers[strategy], s=15)
        ## the mean of this strategy, bigger and in colour, with the SD as error bars
        plt.errorbar(numpy.mean(times), numpy.mean(devs),
                     xerr=numpy.std(times), yerr=numpy.std(devs),
                     color=colors[strategy], marker=markers[strategy], markersize=10,
                     capsize=4, label=strategy)

    plt.xlabel("Total trial time (ms)")
    plt.ylabel("Max lateral deviation (m)")
    plt.legend()
    plt.show()



## Engineering 3B1, plotting a single trial is switched off so the simulations run fast
## To plot one trial again, runTrial() also has to return locPos and locColor
if __name__ == "__main__":
    #trialTime, locPos, locColor = runTrial(interleaving="drivingOnly")
    #plotTrial(trialTime, locPos, locColor)
    runSimulations()
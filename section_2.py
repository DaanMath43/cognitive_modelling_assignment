import matplotlib.pyplot as plt
import numpy
from itertools import product
import math
import driver_model

###
### Section 2: Applied scenario: E-mailing while driving 
###

##
## SERVES AS A BACKUP
##

def drift(pos, duration, locPos, locColor):
    """Car drifts (no steering) for `duration` ms, one update per 50 ms."""
    dt = driver_model.timeStepPerDriftUpdate
    for i in range(math.floor(duration / dt)):
        pos = pos + driver_model.vehicleUpdateNotSteering() * (dt / 1000)
        locPos.append(pos)
        locColor.append("red")
    return pos


def steer(pos, nrMovements, locPos, locColor):
    """Active steering: nrMovements x 250 ms, position stored every 50 ms.
    Returns the new position and the time spent steering."""
    dt = driver_model.timeStepPerDriftUpdate
    for k in range(nrMovements):
        latVel = driver_model.vehicleUpdateActiveSteering(abs(pos))   # once per 250 ms
        for i in range(math.floor(driver_model.steeringUpdateTime / dt)):
            if pos > 0:
                pos = pos - latVel * (dt / 1000)
            else:
                pos = pos + latVel * (dt / 1000)
            locPos.append(pos)
            locColor.append("blue")
    return pos, nrMovements * driver_model.steeringUpdateTime

def runTrial(nrWordsPerSentence=5, nrSentences=3, nrSteeringMovementsWhenSteering=2, interleaving="word"):
    driver_model.resetParameters()
    locPos = []
    locColor = []
    trialTime = 0
    pos = driver_model.startingPositionInLane

    # typing speed: drawn once per trial, shared by all strategies
    wpm = numpy.random.normal(driver_model.wordsPerMinuteMean, driver_model.wordsPerMinuteSD)
    wpm = max(wpm, 1)
    timePerWord = 60000 / wpm

    if interleaving == "word":
        for s in range(nrSentences):
            for w in range(nrWordsPerSentence):
                wordTime = timePerWord + driver_model.retrievalTimeWord
                if w == 0:
                    wordTime += driver_model.retrievalTimeSentence
                trialTime += wordTime
                pos = drift(pos, wordTime, locPos, locColor)

                lastWord = (s == nrSentences - 1) and (w == nrWordsPerSentence - 1)
                if not lastWord:
                    pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                    trialTime += steerTime

    elif interleaving == "sentence":
        for s in range(nrSentences):
            # whole sentence in one go: sentence retrieval + all words, no per-word retrieval
            sentenceTime = driver_model.retrievalTimeSentence + nrWordsPerSentence * timePerWord
            trialTime += sentenceTime
            pos = drift(pos, sentenceTime, locPos, locColor)

            if s < nrSentences - 1:          # no steering after the last sentence
                pos, steerTime = steer(pos, nrSteeringMovementsWhenSteering, locPos, locColor)
                trialTime += steerTime

    return trialTime, locPos, locColor
    
    

def plotTrial(trialTime, locPos, locColor):
    # x-axis: each position is one 50 ms step -> convert step index to ms
    times = [i * driver_model.timeStepPerDriftUpdate for i in range(len(locPos))]

    meanPos = numpy.mean(numpy.abs(locPos))   # how far from centre on average
    maxPos = numpy.max(numpy.abs(locPos))     # furthest from centre, regardless of side

    plt.scatter(times, locPos, c=locColor, s=8)
    plt.xlabel("Time (ms)")
    plt.ylabel("Lane position (m)")
    plt.title(f"Total trial time = {trialTime:.0f} ms; "
              f"Mean position on the road = {meanPos:.3f} m; "
              f"Max position on the road (absolute) = {maxPos:.3f} m", fontsize=8)
    plt.show()

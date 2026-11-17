import matplotlib.pyplot as plt
import numpy
from itertools import product
import math

###
### Section 1a: Model Human Processor (Card, Moran & Newell, 1983) - simple reaction task
###

## Step A: stimulus appears at t = 0, nothing has happened yet
def start():
    return 0    ### ms

## Step B: perceptual processor (p)
def perceptualstep(type="middle"):
    if type == "middle":
        return 100  ### ms
    if type == "fast":
        return 50   ### ms
    if type == "slow":
            return 200   ### ms

## Step C: cognitive processor (c)
def cognitivestep(type="middle"):
    if type == "middle":
        return 70  ### ms
    if type == "fast":
        return 25   ### ms
    if type == "slow":
        return 170   ### ms

## Step D: motor processor (m)
def motorstep(type="middle"):
    if type == "middle":
        return 70  ### ms
    if type == "fast":
        return 30   ### ms
    if type == "slow":
        return 100   ### ms

def example1():
    totalTime = start() + perceptualstep() + cognitivestep() + motorstep()
    return totalTime    ### ms

def example2(completenessValue="extremes"):
    completeness = completenessValue
    speeds = ["fast","middle","slow"]
    totalTime = []
    if completeness == "extremes":  
        for speed in speeds:
            completeness = speed
            totalTime.append(start() + perceptualstep(completeness) + cognitivestep(completeness) + motorstep(completeness))
    elif completeness == "all":
            for p, c, m in product(speeds, repeat=3): 
                total = start() + perceptualstep(p) + cognitivestep(c) + motorstep(m)
                totalTime.append(total)

    plt.boxplot(totalTime)
    plt.ylabel("Total time (ms)")
    plt.title("Model human processor")
    plt.show()
    return totalTime    ### ms

def example3(completeness="extremes"):
    speeds = ["fast", "middle", "slow"]
    totalTime = []

    if completeness == "extremes":
        combos = [(s, s, s) for s in speeds]
    elif completeness == "all":
        combos = product(speeds, repeat=3) 

    for p, c, m in combos:
        total = (start()
                 + perceptualstep(p)   # perceive stimulus 1
                 + perceptualstep(p)   # perceive stimulus 2
                 + cognitivestep(c)    # compare in working memory
                 + cognitivestep(c)    # prepare motor command
                 + motorstep(m))       # execute
        totalTime.append(total)

    return totalTime ### ms    

def example4(completeness="extremes"):
    speeds = ["fast", "middle", "slow"]
    secondStimulusTime = [40, 80, 110, 1150, 210, 240]
    totalTime = []

    if completeness == "extremes":
        combos = [(s, s, s) for s in speeds]
    elif completeness == "all":
        combos = product(speeds, repeat=3)

    for p, c, m in combos:
        total = (start()
                 + perceptualstep(p)   # perceive stimulus 1
                 + perceptualstep(p)   # perceive stimulus 2
                 + cognitivestep(c)    # compare in working memory
                 + cognitivestep(c)    # prepare motor command
                 + motorstep(m))       # execute
        for secondTime in secondStimulusTime:
            totalTime.append(total + secondTime)

    return totalTime  ### ms

def example5(completeness="extremes"):
    speeds = ["fast", "middle", "slow"]
    errorFactor = {"fast": 3, "middle": 2, "slow": 0.5}
    results = []   # list of (time, error) pairs

    if completeness == "extremes":
        combos = [(s, s, s) for s in speeds]
    elif completeness == "all":
        combos = product(speeds, repeat=3)

    for p, c, m in combos:
        steps = [p, p, c, c, m] 

        total = (start()
                 + perceptualstep(p) + perceptualstep(p)
                 + cognitivestep(c) + cognitivestep(c)
                 + motorstep(m))

        error = 0.01
        for s in steps:
            error *= errorFactor[s]
        error = min(error, 1.0)   # cap at 100%

        print(f"p={p}, c={c}, m={m} -> {total} ms, error {error:.4f}")
        print(f"p={p}, c={c}, m={m} -> {total} ms, error {error * 100:.2f}%")
        results.append((total, error * 100))   # convert to percentage

    times, errors = zip(*results)
    plt.scatter(times, errors)                
    plt.xlabel("Trial time (ms)")
    plt.ylabel("Error probability (%)")
    plt.ylim(0, 105)
    plt.title("Speed-accuracy trade-off (example 5)")
    plt.show()

    return results

print(example5("all"))     
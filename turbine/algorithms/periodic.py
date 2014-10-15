'''
Created on Oct 15, 2014

Periodic scheduling related algorithms

@author: bbodin
'''
from generation.generate import generate

def HSDF_starting_time_computation (g, period) :
    
    startingTime = {}
    weight = {}
    startingTime[g.getTaskList()[0]] = 0
    
    # Step 1: initialize graph
    for v in g.getTaskList()[1:] :
        startingTime[v] = float("-inf")

    for c in g.getArcList() :
        u = g.getSource(c)
        weight[c] = sum(g.getPhaseDuration(u)) - g.getInitialMarking(c) * period 

    # Step 2: relax edges repeatedly
    for i in range (len(g.getTaskList())) :
       for c in g.getArcList() :
           u = g.getSource(c)
           v = g.getTarget(c)
           w = weight[c]
           if startingTime[u] + w > startingTime[v]:
               startingTime[v] = startingTime[u] + w
    return startingTime

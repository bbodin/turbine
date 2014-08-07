from math import floor
from random import shuffle, random, sample, randint
import logging

from models.gcd import gcdList, gcd
from models.lcm import lcm


class Error(Exception):
    pass
error = Error  # backward compatibility

def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur.

    Parameters
    ----------
    n : The size of the random list return.
    total : The sum of the list return
    """

    if total < n :
        x = [0] * (n - total) + [1] * total
        shuffle(x)
        return x

    x = [0] * n
    pan = total
    for i in range(n - 1) :
        x[i] = floor(random() * pan)
        pan = pan - x[i]
    x[n - 1] = pan
    return x
    i = 0L
    dividers = sample(xrange(total), n - 1)
    dividers.sort()
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


########################################################################
#                           generate weight                            #
########################################################################
def generateWeight(graph, c_param):
    """The weight generation step of the generator (step 2)
    """
    __generateRV(graph, c_param)  # generate the repetition vector
    __generatePhaseLists(graph, c_param)  # generate weight vectors
    if c_param.isInitialized():
        __generateInitialPhaseLists(graph, c_param)  # generate initial vectors

def __generateRV(graph, c_param):
    """Generate the vector of repetition factor RV with gcd(RV) = 1 and SUM(RV)=sumRV
    """
    logging.info("Generate repetition vector")
    sumRV = c_param.getAverageRepetitionFactor() * graph.getTaskCount()  # Sum of the repetition vector

    RVList = []
    RVTot = 0
    gcdValue = 0
    # Repetition factor are randomly selected 
    for i in xrange(0, graph.getTaskCount()):
        # ~ RV = gaussRandomSelection(1,2*c_param.getAverageRepetitionFactor()-1)
        RV = randint(1, 2 * c_param.getAverageRepetitionFactor() - 1)
        gcdValue = gcd(gcdValue, RV)
        RVList.append(RV)
        RVTot += RV

    # If a problem occurred the list is readjusted
    if RVTot > sumRV :
        for i in xrange(0, RVTot - sumRV):
            if RVList[i % graph.getTaskCount()] > 1 :
                RVList[i % graph.getTaskCount()] -= 1
                RVTot -= 1
    else :
        # The program should never go here or your sum of the repetition vector is too small
        for i in xrange(0, sumRV - RVTot):
            RVList[i % graph.getTaskCount()] += 1
            RVTot += 1

    # Modify the two last integers of the list to get a gcd equal to 1
    if gcdValue != 1 :
        logging.info("recalculate GCD")
        while gcdList([gcdValue, RVList[-1], RVList[-2]]) != 1:
            RVList[-1] -= 1
            RVList[-2] += 1

    shuffle(RVList)

    for task in graph.getTaskList() :
        graph.setRepetitionFactor(task, RVList[task])
    return

def __generatePhaseLists(graph, c_param):    
    """Generate weights of the dataflow.
    """
    logging.info("Generate task phase lists")
    k = 0

    lcmValue = 1
    for  task in graph.getTaskList():
        lcmValue = lcm(lcmValue, graph.getRepetitionFactor(task))

    # ~ start = time.time()
    for task in graph.getTaskList():
        phaseCount = randint(c_param.getMinPhaseCount(), c_param.getMaxPhaseCount())
        Zi = lcmValue / graph.getRepetitionFactor(task)
        if Zi == 0:
            logging.fatal("lcmValue" + str(lcmValue))
            logging.fatal("null rate when generating, this error should never occur...")
            raise Error("__generatePhaseLists", "null rate when generating, this error should never occur...")

        phaseDurationList = constrained_sum_sample_pos(phaseCount, randint(1, c_param.getAverageTime() * phaseCount * 2 - 1))

        graph.setPhaseCount(task, phaseCount)
        graph.setPhaseDurationList(task, phaseDurationList)

        for arc in graph.getArcList(source=task) :
            prodList = constrained_sum_sample_pos(phaseCount, Zi)
            graph.setProdList(arc, prodList)
            if sum(graph.getProdList(arc)) != Zi :
                print graph.getProdList(arc)
                print Zi
                logging.fatal("constrained_sum_sample_pos return wrong list, it's generally cause by too large number.")
                raise Error("__generatePhaseLists", "constrained_sum_sample_pos return wrong list, it's generally cause by too large number.")
            
        for arc in graph.getArcList(target=task) :
            consList = constrained_sum_sample_pos(phaseCount, Zi)
            graph.setConsList(arc, consList)
            if c_param.isThresholded():
                consThresholdList = constrained_sum_sample_pos(phaseCount, Zi)
                graph.setConsThresholdList(arc, consThresholdList)
            if sum(graph.getConsList(arc)) != Zi :
                logging.fatal("constrained_sum_sample_pos return wrong list, it's generally cause by too large number.")
                raise Error("__generatePhaseLists", "constrained_sum_sample_pos return wrong list, it's generally cause by too large number.")

        if graph.getTaskCount() > 1000 and k % 1000 == 0 :
            logging.info(str(k) + "/" + str(graph.getTaskCount()) + " tasks weigth generation complete.")
        k += 1 

def __generateInitialPhaseLists(graph, c_param):
    """Generate initial weights of the dataflow.
    """
    if (c_param.isInitialized() == False) or (c_param.getMaxPhaseCountInit() == 0) :  # TODO : fix temporaire

        for task in graph.getTaskList() :
            graph.setPhaseCountInit(task, 0) 
            graph.setPhaseDurationInitList(task, [])
        for arc in graph.getArcList() :            
            graph.setProdInitList(arc, [])
            graph.setConsInitList(arc, [])
        return

    logging.info("Generate initial task phase list")
    k = 0
    for task in graph.getTaskList() :
        phaseCountInit = randint(c_param.getMinPhaseCountInit(), c_param.getMaxPhaseCountInit())
        if phaseCountInit == 0 :
            graph.setPhaseCountInit(task, phaseCountInit)
            graph.setPhaseDurationInitList(task, [])
            for arc in graph.getArcList(source=task) :            
                graph.setProdInitList(arc, [])
            for arc in graph.getArcList(target=task) :  
                graph.setConsInitList(arc, [])
            continue
        phaseDurationInitList = constrained_sum_sample_pos(phaseCountInit, randint(1, c_param.getAverageTimeInit() * phaseCountInit * 2 - 1))
        graph.setPhaseCountInit(task, phaseCountInit)
        graph.setPhaseDurationInitList(task, phaseDurationInitList)

        # ~ iniZi = gaussRandomSelection(phaseCountInit,c_param.getMAX_INIT_TOT_WEIGHT())
        iniZi = randint(1, c_param.getAverageWeightInit() * phaseCountInit - 1)


        for arc in graph.getArcList(source=task) :
            iniProdList = constrained_sum_sample_pos(phaseCountInit, iniZi)
            graph.setProdInitList(arc, iniProdList)

        for arc in graph.getArcList(target=task) :
            ConsInitList = constrained_sum_sample_pos(phaseCountInit, iniZi)
            graph.setConsInitList(arc, ConsInitList)
            if c_param.isThresholded():
                ConsInitThresholdList = constrained_sum_sample_pos(phaseCountInit, iniZi)
                graph.setConsInitThresholdList(arc, ConsInitThresholdList)
            
        if graph.getTaskCount() > 1000 and k % 1000 == 0 :
            logging.info(str(k) + "/" + str(graph.getTaskCount()) + " tasks initial weigth generation complete.")
        k += 1

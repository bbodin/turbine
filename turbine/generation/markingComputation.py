import logging

from algorithms.solve_SC1 import SolverSC1
from algorithms.solve_SC2 import SolverSC2


def __sumPreload(graph):
    tot = 0
    for edge in graph.getArcList() :
        tot += graph.getInitialMarking(edge)
    return tot

def __clearInitialMarking(graph):
    for edge in graph.getArcList() :
        graph.setInitialMarking(edge, 0)


########################################################################
#                           generate preload                           #
########################################################################
def generateInitialMarking(graph, solver="auto", GLPKVerbose=False, LPFileName=None):
    """Step 3
    """
    __clearInitialMarking(graph)

    if solver == "SC2" :
        solver = SolverSC2(graph, GLPKVerbose, LPFileName)
    elif solver == "SC1" :
        solver = SolverSC1(graph, GLPKVerbose, LPFileName)
    elif solver == "None":
        return
    elif solver == "auto" :
        if __SC2RowCount(graph) < __SC1RowCount(graph) :
            solver = SolverSC2(graph, GLPKVerbose, LPFileName)
            logging.info("choose solver SC2")
        else:
            solver = SolverSC1(graph, GLPKVerbose, LPFileName)
            logging.info("choose solver SC1")
    else :
        logging.error("solver : wrong argument")
        return

    solver.generateInitialMarking()
    M0tot = __calcReEntrant(graph)
    logging.info("Mem tot (reentrant) : " + str(M0tot))
    

def __SC2RowCount(graph):
    FRowCount = graph.getArcCount()
    rowCount = 0
    for task in graph.getTaskList():
        taskReEntrant = 0
        for arc in graph.getInputArcList(task):
            if graph.isArcReEntrant(arc) :
                taskReEntrant += 1
        FRowCount -= taskReEntrant
        rowCount += ((graph.getInputDegree(task) - taskReEntrant) * (graph.getOutputDegree(task) - taskReEntrant))
    return rowCount + FRowCount

def __SC1RowCount(graph):
    rowCount = 0
    for arc in graph.getArcList():
        source = graph.getSource(arc)
        target = graph.getTarget(arc)
        if not graph.isArcReEntrant(arc) :
            if graph.isInitialized() :
                sourcePhaseCount = graph.getPhaseCount(source) + graph.getPhaseCountInit(source)
                targetPhaseCount = graph.getPhaseCount(target) + graph.getPhaseCountInit(target)
                rowCount += sourcePhaseCount * targetPhaseCount
            else :
                rowCount += graph.getPhaseCount(source) * graph.getPhaseCount(target)
    return rowCount

def __calcReEntrantPreload(graph):
    M0tot = 0
    for arc in graph.getArcList() :
        if graph.isArcReEntrant(arc) :
            cons = graph.getConsList(arc)
            if graph.isInitialized():
                cons += graph.getConsInitList(arc)

            step = graph.getGcd(arc)
            M0 = sum(cons) - step
            
            if M0 % step != 0 or M0 == 0:
                M0 += (step - M0 % step)

            graph.setInitialMarking(arc, M0)
            M0tot += M0
            logging.debug("Reentrant initial marking for arc : " + str(arc) + " : " + str(M0))
    return M0tot

def __calcReEntrant(graph):
    M0tot = 0
    for arc in graph.getArcList() :
        if graph.isArcReEntrant(arc) :
            phaseCount = graph.getPhaseCount(graph.getTarget(arc))
            prodList = graph.getProdList(arc)
            consList = graph.getConsList(arc)
            thresholdList = graph.getConsThresholdList(arc)
            if graph.isInitialized() :
                phaseCount += graph.getPhaseCountInit(graph.getTarget(arc))
                prodList = graph.getProdInitList(arc) + prodList
                consList = graph.getConsInitList(arc) + consList
                thresholdList = graph.getConsInitThresholdList(arc) + thresholdList
        
            retMax = graph.getConsList(arc)[0]
        
            predOut = 0
            predIn = 0
            In = 0
            for phase in xrange(phaseCount):
                if phase > 0 :
                    predOut += prodList[phase - 1]
                    predIn += consList[phase - 1]
                In += consList[phase]
        
                W2 = In - predOut
                if graph.isThresholded() :
                    W2 += predIn + thresholdList[phase] - In
        
                if retMax < W2 : retMax = W2
                graph.setInitialMarking(arc, retMax)
                M0tot += retMax
                logging.debug("Reentrant initial marking for arc : " + str(arc) + " : " + str(retMax))

    return M0tot
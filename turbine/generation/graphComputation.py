from models.gcd import *
from models.graph import Graph
from models.lcm import *
from random import *
import logging


def __getRandomTask(graph):
    return graph.getTaskList()[randint(0,graph.getTaskCount()-1)]

########################################################################
#                           generate graph                             #
########################################################################
def generateGraph(graphName, c_param):
    """Step 1
    """
    graph = Graph(graphName)
    __generateConnexGraph(graph,c_param)#Generate a Tree graph
    __generateArcs(graph,c_param)#Add arcs to the Tree graph
    return graph

def __generateConnexGraph(graph,c_param):
    logging.info("Generate connex graph")
    graph.addTask()
    for i in xrange(1,c_param.getNbTask()) :
        task = graph.addTask()
        randomTask = __getRandomTask(graph)
        while randomTask == task :
            randomTask = __getRandomTask(graph)
        if randint(0,1) : graph.addArc(task,randomTask)
        else : graph.addArc(randomTask,task)
        if graph.getTaskCount() > 1000 and  i%1000 == 0 :
            logging.info(str(i)+"/"+str(c_param.getNbTask())+" tasks generate.")

def __generateArcs(graph, c_param):
    logging.info("Generate more arcs")
    
    inTask = []
    outTask = []

    #We begin with the generation of in channel
    for i in xrange(0,graph.getTaskCount()):
        arcsInCount = randint(c_param.getMinArcsCount(),c_param.getMaxArcsCount())

        #random number of arcs for each tasks - 1 because each task already have one arc.
        if graph.getInputDegree(i) > 0 :
            arcsInCount-=1
        inTask+= [i]*arcsInCount
    shuffle(inTask)

    #Generation of out channel depending of reentrant option
    if not c_param.isNotreentrant():
        for i in xrange(0,graph.getTaskCount()):
            arcsOutCount = randint(c_param.getMinArcsCount(),c_param.getMaxArcsCount())
            #random number of arcs for each tasks - 1 because each task already have one arc.
            if graph.getOutputDegree(i) > 0 :
                arcsOutCount-=1
            outTask+= [i]*arcsOutCount
        shuffle(outTask)
    else : #NoReentrant part
        for elem in inTask :
            out = randint(0, graph.getTaskCount()-1)
            while out == elem:
                out = randint(0, graph.getTaskCount()-1)
            outTask+=[out]


    nbTotArcs = min(len(inTask), len(outTask))
    for i in xrange(0,nbTotArcs):
        graph.addArc(outTask[i],inTask[i])
        if graph.getTaskCount() > 1000 and  i%1000 == 0 :
            logging.info(str((i+1)+graph.getTaskCount())+"/"+str(nbTotArcs+graph.getTaskCount())+" arcs added.")

'''
Created on Jul 4, 2014

@author: lesparre
'''
from generation.graphComputation import __generateConnexGraph
from generation.ratesComputation import  generateWeight
from models.graph import Graph
from random import randint, randrange
import logging
import param.parameters
import random
import time

import networkx as nx


def generate(graphName = "generated_graph", c_param = None):
    """Generate a dataflow graph acyclique according to the parameters c_param
    
    Parameters
    ----------
    graphName : the name of the dataflow (default : generated_graph).
    c_param : parameters of the generation.
    """
    logging.basicConfig(level=c_param.getLoggingLevel())

    if c_param == None :
        c_param = param.parameters.Parameters()
        
    start = time.time()
    logging.info("Generating graph")
    graph = Graph(graphName)
    __generateConnexGraph(graph, c_param)#Generate a Tree graph
    __generateArcs(graph, c_param)
    logging.info("Generating weight")
    generateWeight(graph, c_param)
    __generateInitialMarking(graph)
    logging.info("Generating done : "+str(time.time() - start)+"s")
    return graph

def __generateArcs(graph, c_param):
    """Randomly add arcs in the graph such as it stay acyclique.
    A topological list is used to add arcs.
    
    Parameters
    ----------
    graphName : the name of the dataflow (default : generated_graph).
    c_param : parameters of the generation.
    """
    topologicalList = nx.topological_sort(graph.nxg)
    for k in xrange(len(topologicalList)-1) :
        task = topologicalList[k]
        arcsOutCount = randint(c_param.getMinArcsCount(),c_param.getMaxArcsCount())
        for i in xrange(arcsOutCount):
            target = random.choice(topologicalList[(k+1):])
            graph.addArc(task, target)

def __generateInitialMarking(graph):
    for arc in graph.getArcList():
        i = randint(1,10)
        min_ = min(sum(graph.getProdList(arc)),sum(graph.getConsList(arc)))
        max_ = max(sum(graph.getProdList(arc)),sum(graph.getConsList(arc)))
        initialMarking = randint(i*min_,i*max_)
        graph.setInitialMarking(arc, initialMarking)
    graph.printBuffer()
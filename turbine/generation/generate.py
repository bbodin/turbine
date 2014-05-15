from generation.graphComputation import generateGraph
from generation.markingComputation import  generateInitialMarking
from generation.ratesComputation import  generateWeight
import param.parameters
import time
import logging


def generate(graphName = "generated_graph", c_param = None):

    logging.basicConfig(level=c_param.getLoggingLevel())

    if c_param == None :
        c_param = param.parameters.Parameters()
        
    start = time.time()
    logging.info("Generating graph")
    graph = generateGraph(graphName, c_param)
    logging.info("Generating weight")
    generateWeight(graph, c_param)
    logging.info("Generating initial marking")
    generateInitialMarking(graph, solver = c_param.getSolver(), LPFileName = c_param.getLPFileName())
    logging.info("Generating done : "+str(time.time() - start)+"s")
    return graph
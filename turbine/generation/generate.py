from generation.graphComputation import generateGraph
from generation.markingComputation import  generateInitialMarking
from generation.ratesComputation import  generateWeight
import param.parameters
import time
import logging


def generate(graphName = "generated_graph", c_param = None):
    """Generate a dataflow graph according to the parameters c_param
    
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
    graph = generateGraph(graphName, c_param)
    logging.info("Generating weight")
    generateWeight(graph, c_param)
    logging.info("Generating initial marking")
    generateInitialMarking(graph, solver = c_param.getSolver(), GLPKVerbose = c_param.isGLPKVerbose(), LPFileName = c_param.getLPFileName())
    logging.info("Generating done : "+str(time.time() - start)+"s")
    return graph
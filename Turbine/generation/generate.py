import logging
from time import time

from marking_computation import compute_initial_marking
from rates_computation import generate_rates
from graph_computation import generate_dataflow
from Turbine.param.parameters import Parameters


def generate(dataflow_name="generated_graph", c_param=None):
    """Generate a dataflow graph according to the parameters c_param
    
    Parameters
    ----------
    graphName : the name of the dataflow (default : generated_graph).
    c_param : parameters of the generation.
    """
    if c_param is None:
        c_param = Parameters()
    logging.basicConfig(level=c_param.get_logging_level())

    start = time()
    logging.info("Generating graph")
    dataflow = generate_dataflow(dataflow_name, c_param)
    logging.info("Generating weight")
    generate_rates(dataflow, c_param)
    compute_initial_marking(dataflow,
                            solver_str=c_param.get_solver(),
                            solver_verbose=c_param.is_solver_verbose(),
                            lp_filename=c_param.get_lp_filenam())

    logging.info("Generating done : " + str(time() - start) + "s")
    return dataflow

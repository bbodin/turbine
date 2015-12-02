"""
Example of how to generate a Synchronous Dataflow Graph
"""
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation #####"
c_param = Parameters()

# Set the SDF type for the generation
c_param.set_dataflow_type("SDF")

# Min/Max arcs count per task 
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(3)

# Number of task in the dataflow
c_param.set_nb_task(100)

print "###### Generate SDF dataflow ########"
SDFG = generate("Test_of_SDFG", c_param)
print SDFG

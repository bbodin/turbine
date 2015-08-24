"""
Example of how to generate a Synchronous Dataflow Graph
"""
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation #####"
c_param = Parameters()

# Set the SDF type for the generation
c_param.set_dataflow_type("SDF")

# Set the SDF type for the generation
c_param.set_acyclic(True)

# Min/Max arcs count per task 
c_param.set_min_arcs_count(1)
c_param.set_max_arcs_count(5)

# Number of task in the dataflow
c_param.set_nb_task(10)

print "###### Generate SDF dataflow ########"
SDFG = generate("Test_of_SDFG", c_param)
print SDFG
print "Cyclic graph:", SDFG.is_cyclic

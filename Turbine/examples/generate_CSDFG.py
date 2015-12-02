"""
Example of how to generate a Cyclo-Static dataflow graph
"""
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the CSDF generation ####"
c_param = Parameters()

# Set the CSDF type for the generation
c_param.set_dataflow_type("CSDF")

# Min/Max phase per task
c_param.set_min_phase_count(1)
c_param.set_max_phase_count(10)

# Min/Max arcs count per task 
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(3)

# Number of task in the dataflow
c_param.set_nb_task(100)

print "###### Generate CSDF dataflow #######"
CSDFG = generate("Test_of_SDFG", c_param)
print CSDFG

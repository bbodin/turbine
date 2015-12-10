"""
Example of how to generate a Phased Computation Graph
"""
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the PCG generation #####"
c_param = Parameters()

# Set the PCG type for the generation
c_param.set_dataflow_type("PCG")

# Min/Max phase per task
c_param.set_min_phase_count(1)
c_param.set_max_phase_count(10)

# Min/Max initial phase per task
c_param.set_min_ini_phase_count(1)
c_param.set_max_ini_phase_count(5)

# Min/Max arcs count per task
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(3)

# Number of task in the dataflow
c_param.set_nb_task(100)

print "###### Generate PCG dataflow ########"
PCG = generate("Test_of_SDFG", c_param)
PCG.compute_repetition_vector()
print PCG

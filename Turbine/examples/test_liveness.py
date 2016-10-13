import logging

from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation #####"
c_param = Parameters()
c_param.set_dataflow_type("SDF")
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(5)
c_param.set_nb_task(100)

print "###### Generate dataflow ############"
dataflow = generate("SDF_of_test", c_param)  # Generate a SDF dataflow graph
print dataflow
print "###### Compute the symbolic execution to find dead lock ##"
print "Is dead lock:", dataflow.is_dead_lock

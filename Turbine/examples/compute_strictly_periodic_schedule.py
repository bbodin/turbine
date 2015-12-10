from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation ###########"
c_param = Parameters()
c_param.set_dataflow_type("SDF")
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(5)
c_param.set_nb_task(10)

print "###### Generate dataflow ##################"
dataflow = generate("SDF_of_test", c_param)  # Generate a SDF dataflow graph

print "###### Compute strictly periodic schedule #"
period = dataflow.get_period(True)  # Compute the period of the dataflow
# Parameter True display start time of each task of the dataflow
# The get the period of each task:
for task in dataflow.get_task_list():
    print "period of task "+str(task)+": "+str(period/dataflow.get_repetition_factor(task))

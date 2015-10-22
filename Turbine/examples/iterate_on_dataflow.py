from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

c_param = Parameters()

# Set the SDF type for the generation
c_param.set_dataflow_type("SDF")

# Min/Max arcs count per task
c_param.set_min_arcs_count(1)
c_param.set_max_arcs_count(3)

# Number of task in the dataflow
c_param.set_nb_task(10)

# Generate a dataflow for the example
SDFG = generate("Test_of_SDFG", c_param)

# Iterate on tasks
for task in SDFG.get_task_list():
    print task, SDFG.get_task_name(task)

# Iterate on arcs:
for arc in SDFG.get_arc_list():
    print arc, SDFG.get_arc_name(arc)

# get_arc_list method can do much more
task_t0 = SDFG.get_task_list()[0]  # The first task
for arc in SDFG.get_arc_list(source=task_t0):
    print arc  # Display every output arcs of the task

for arc in SDFG.get_arc_list(target=task_t0):
    print arc  # Display every input arcs of the task

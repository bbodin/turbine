from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation #####"
c_param = Parameters()
c_param.set_dataflow_type("SDF")
c_param.set_solver(None)  # pass the initial marking computation phase when generate the dataflow
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(5)
c_param.set_nb_task(100)

print "###### Generate dataflow ############"
dataflow = generate("SDF_of_test", c_param)  # Generate a SDF dataflow graph
print dataflow  # Print information about the dataflow, as you can see it's not normalized
print "Is dead lock:", dataflow.is_dead_lock  # Verify if the dataflow is live (Use symbolic execution: can be long on

print  "###### Compute the initial marking ##"
dataflow.compute_initial_marking()  # Compute the minimal initial marking
# By default the initial marking solver is choose automatically between SC1 and SC2.
# The first one is more efficient on SDF and the second one is more efficient on CSDF and PCG.
# You can force them with the argument solver_str="SC1" or solver_str="SC2"
# solver_str=None is to avoid solving the initial marking.
# solver_str="SC1_MIP" use the solver Gurobi and gives better result than SC1 and SC2 but it cannot handle big graphs
print dataflow
print "Is dead lock:", dataflow.is_dead_lock  # Verify if the dataflow is live (Use symbolic execution: can be long on
# big graphs)

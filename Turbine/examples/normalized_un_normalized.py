"""
Example of how to write and read TUR files.

TUR files are not XML, they are 10 times smaller than SDF3 files and easy to write by hand.
"""
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation #####"
c_param = Parameters()
c_param.set_dataflow_type("SDF")
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(5)
c_param.set_nb_task(10)

print "###### Generate dataflow ############"
SDFG = generate("Test_of_SDF", c_param)
print SDFG
# The graph is not generate normalized, first we normalized it
print "####### Normalized graph ############"
coef_vector = SDFG.normalized()
print SDFG
# coef_vector is the un-normalization vector to retrieve the original graph.
# It's a dictionary {arc:coef}
print "####### Un-normalized graph #########"
# The graph can be un-normalized with a random vector if you put no parameters in the function un_normalized()
# Here we want to retrieve the original generated graph so we call the un_normalization with the proper argument
SDFG.un_normalized(coef_vector)
print SDFG

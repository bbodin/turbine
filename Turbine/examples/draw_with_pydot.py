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
c_param.set_max_task_degree(3)
c_param.set_nb_task(10)

print "###### Generate dataflow ############"
SDFG = generate("Test_of_SDF", c_param)

print "####### Draw File ###################"
# Work with CSDF or PCG as well !
SDFG.draw_to_pdf("pdfname")  # without .pdf !
print SDFG

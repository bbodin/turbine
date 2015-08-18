"""
Example of how to write and read TUR files.

TUR files are not XML, they are 10 times smaller than SDF3 files and easy to write by hand.
"""
from Turbine.file_parser.turbine_parser import write_tur_file, read_tur_file
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation #####"
c_param = Parameters()
c_param.set_dataflow_type("SDF")
c_param.set_min_arcs_count(1)
c_param.set_max_arcs_count(5)
c_param.set_nb_task(100)

print "###### Generate dataflow ############"
SDFG = generate("Test_of_SDF", c_param)

print "####### Write tur file ##############"
write_tur_file(SDFG, "SDF.tur")

print "####### Write tur file ##############"
SDF_from_file = read_tur_file("SDF.tur")
print SDFG

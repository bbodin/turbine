"""
Example of how to write and read SDF3 files.
"""
from Turbine.file_parser.sdf3_parser import write_sdf3_file, read_sdf3_file
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters

print "###### Setup the SDF generation #####"
c_param = Parameters()
c_param.set_dataflow_type("SDF")
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(2)
c_param.set_nb_task(5)

print "###### Generate dataflow ############"
SDFG = generate("SDF_of_test", c_param)  # Generate a SDF for the example.
print SDFG

print "####### Write sdf3 file #############"
write_sdf3_file(SDFG, "SDF.sdf3")  # Write the generated SDF in a sdf3 file.

print "####### Read sdf3 file ##############"
SDF_from_file = read_sdf3_file("SDF.sdf3")  # Read the SDF from the file write previously sdf3 file.
print SDF_from_file

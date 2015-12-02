"""
Illustrate how to convert a sdf3 file into a tur file
"""

from Turbine.file_parser.sdf3_parser import write_sdf3_file, read_sdf3_file
from Turbine.file_parser.turbine_parser import write_tur_file
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters


print "###### Setup the SDF generation #####"
c_param = Parameters()
c_param.set_dataflow_type("SDF")
c_param.set_min_task_degree(1)
c_param.set_max_task_degree(5)
c_param.set_nb_task(100)

print "###### Generate dataflow ############"
SDFG = generate("Test_of_SDF", c_param)  # Generate a SDF
print SDFG

print "####### Write sdf3 file #############"
write_sdf3_file(SDFG, "SDF.sdf3")  # Write the SDF as a sdf3 file (XML)

print "####### Read sdf3 file ##############"
SDF_from_file = read_sdf3_file("SDF.sdf3")  # Read the SDF from the sdf3 file write the previous line

print "####### Write tur file ##############"
write_tur_file(SDF_from_file, "SDF.tur")  # Write the SDF as a tur file

print "done !"

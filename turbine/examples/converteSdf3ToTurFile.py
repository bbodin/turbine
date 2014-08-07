'''
Created on Jul 4, 2014

@author: lesparre
'''

from file_parser.sdf3_parser import write_sdf3_file, read_sdf3_file
from file_parser.turbine_parser import write_tur_file
from generation.generate import generate
import param.parameters


# Prepare a sdf3 file for the example
c_param = param.parameters.Parameters()
c_param.setMinPhaseCount(1)
c_param.setMaxPhaseCount(1)
c_param.setMaxPhaseCountInit(0)
c_param.setIsThreshold(False)
c_param.setMinArcsCount(1)
c_param.setMaxArcsCount(5)
c_param.setNbTask(100)
SDFexample = generate("Test_of_SDF", c_param)
write_sdf3_file(SDFexample, "SDF.sdf3")

# Read a sdf3 format dataflow names "PCG.sdf3
SDFfromFile = read_sdf3_file("SDF.sdf3")

# Write the dataflow in the tur format
write_tur_file(SDFfromFile, "SDF.tur")

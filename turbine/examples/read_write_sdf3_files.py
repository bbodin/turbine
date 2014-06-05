'''
Created on Jun 5, 2014

Example of how to write and read SDF3 files.

@author: lesparre
'''

from generation.generate import generate
import param.parameters

from parser.sdf3_parser import write_sdf3_file, read_sdf3_file

#Setup the PCG generation.
c_param= param.parameters.Parameters()
c_param.setMinPhaseCount(1)
c_param.setMaxPhaseCount(5)
c_param.setIsInitialized(True)
c_param.setMinPhaseCountInit(1)
c_param.setMaxPhaseCountInit(5)
c_param.setIsThreshold(True)
c_param.setMinArcsCount(1)
c_param.setMaxArcsCount(5)
c_param.setNbTask(100)

#Generate a PCG
PCG = generate("Test_of_PCG", c_param)

#Write the dataflow in the SDF3 format
write_sdf3_file(PCG, "PCG.sdf3")

#Read the dataflow
PCGfromFile = read_sdf3_file("PCG.sdf3")

print "###########Generate file###########"
PCG.printInfo()

print "###########read file###########"
PCGfromFile.printInfo()

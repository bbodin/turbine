'''
Created on Jun 5, 2014

Example of how to write and read TUR files.

TUR files are note XML, they are 10 times samller than SDF3 files and easy to write by hand.

@author: lesparre
'''

from generation.generate import generate
import param.parameters

from parser.turbine_parser import read, write

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

#Write the dataflow in the TUR format
write(PCG, "PCG.tur")

#Read the dataflow
PCGfromFile = read("PCG.tur")

print "###########Generate file###########"
PCG.printInfo()

print "###########read file###########"
PCGfromFile.printInfo()

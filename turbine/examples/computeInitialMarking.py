'''
Created on Jun 5, 2014

Example of how to compute the initial marking of a graph.

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
print "#################generated graph#################"
PCG.printInfo()

#Set all initial marking to 0
PCG.clearInitialMarking()
print "#################cleared graph#################"
PCG.printInfo()

#Set all initial marking to 0
PCG.computeInitialMarking()
print "#################compute graph#################"
PCG.printInfo()

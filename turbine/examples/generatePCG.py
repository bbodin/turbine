'''
Created on Jun 5, 2014

Example of how to generate a PCG (with phases, initial phases and thresholds)

@author: lesparre
'''

from generation.generate import generate
import param.parameters

#Parameters of the generator.
c_param= param.parameters.Parameters()

#Min/Max phase number of tasks.
c_param.setMinPhaseCount(1)
c_param.setMaxPhaseCount(5)

#Allow and setup initial phases
c_param.setIsInitialized(True)
c_param.setMinPhaseCountInit(1)
c_param.setMaxPhaseCountInit(5)

#Allow Thresholds
c_param.setIsThreshold(True)

#Min/Max arcs count per task 
c_param.setMinArcsCount(1)
c_param.setMaxArcsCount(5)

#Task number of the dataflow
c_param.setNbTask(100)

PCG = generate("Test_of_PCG", c_param)
PCG.printInfo()

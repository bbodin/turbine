'''
Created on Jun 5, 2014

Example of how to test the liveness of the graph by executing a symbolic execution.

@author: lesparre
'''

from generation.generate import generate
import param.parameters

#Parameters of the generator.
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

PCG = generate("Test_of_PCG", c_param)
PCG.symbolicExecution()

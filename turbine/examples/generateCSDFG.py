'''
Created on Jun 5, 2014

Example of how to generate a CSDFG (with phases but no initial phases, and no thresholds)

@author: lesparre
'''

from generation.generate import generate
import param.parameters

#Parameters of the generator.
c_param= param.parameters.Parameters()

#Min/Max phase number of tasks.
c_param.setMinPhaseCount(1)
c_param.setMaxPhaseCount(5)

#No initial phases
c_param.setIsInitialized(False)

#No thresholds
c_param.setIsThreshold(False)

#Min/Max arcs count per task 
c_param.setMinArcsCount(1)
c_param.setMaxArcsCount(5)

#Task number of the dataflow
c_param.setNbTask(100)

CSDFG = generate("Test_of_CSDFG", c_param)
CSDFG.printInfo()

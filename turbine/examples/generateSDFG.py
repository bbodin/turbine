#!/usr/bin/python 
'''
Created on Jun 5, 2014

Example of how to generate a SDFG (no phases, no initial phases, and no thresholds)

@author: lesparre
'''

from generation.generate import generate
import param.parameters


# Parameters of the generator.
c_param = param.parameters.Parameters()

# Only one phase
c_param.setMinPhaseCount(1)
c_param.setMaxPhaseCount(1)

# No initial phases
c_param.setIsInitialized(False)

# No thresholds
c_param.setIsThreshold(False)

# Min/Max arcs count per task 
c_param.setMinArcsCount(1)
c_param.setMaxArcsCount(5)

# Task number of the dataflow
c_param.setNbTask(100)

SDFG = generate("Test_of_SDFG", c_param)
SDFG.printInfo()

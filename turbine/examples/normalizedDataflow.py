'''
Created on Jun 5, 2014

Example of how to normalized and denormalized a dataflow graph

@author: lesparre
'''

from generation.generate import generate
import param.parameters


# Setup the PCG generation.
c_param = param.parameters.Parameters()
c_param.setMinPhaseCount(1)
c_param.setMaxPhaseCount(1)
c_param.setIsInitialized(False)
c_param.setIsThreshold(False)
c_param.setMinArcsCount(1)
c_param.setMaxArcsCount(5)
c_param.setNbTask(10)

# Generate a PCG (by default the dataflow graph  is normalized) 
SDF = generate("Test_of_SDF", c_param)
print "#################Generated graph#################"
SDF.printInfo()

# Get the smallest denormalized dataflow graph possible (or you can also specified a vector in "getUnNormalizedGraph()")
SDF.getUnNormalizedGraph()
print "#################deNormalized graph#################"
SDF.printInfo()

# Get the normalized dataflow graph
SDF.getNormalizedGraph()
print "#################Normalized graph#################"
SDF.printInfo()

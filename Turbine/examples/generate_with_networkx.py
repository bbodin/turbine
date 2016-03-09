"""
Example of how to generate a Synchronous Dataflow Graph
"""
from Turbine.generation.generate import generate
from Turbine.param.parameters import Parameters
from networkx import MultiDiGraph
import networkx as nx

print "###### Setup the SDF generation #####"
c_param = Parameters()

# Set the SDF type for the generation
c_param.set_dataflow_type("SDF")

# Generate a random graph using networkx
nx_graph = nx.balanced_tree(2, 10, create_using=MultiDiGraph())

print "###### Generate SDF dataflow ########"
SDFG = generate("Test_of_SDFG", c_param, nx_graph=nx_graph)
print SDFG

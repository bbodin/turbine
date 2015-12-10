import logging
import os

from generation.generate import generate
from file_parser.sdf3_parser import write_sdf3_file, read_sdf3_file
from file_parser.turbine_parser import write_tur_file, read_tur_file
from param.parameters import Parameters


def try_function(function, args):
    try:
        ret = function(*args)
    except:
        print "FAIL !"
    else:
        print "DONE !"
        return ret


def try_property(function):
    try:
        ret = function
    except:
        print "FAIL !"
    else:
        print "DONE !"
        return ret


print "Starting basic test !"

print ""

print "Acyclic SDF generation",
c_param = Parameters()
c_param.set_logging_level(logging.CRITICAL)
c_param.set_multi_graph(True)
c_param.set_reentrant(True)
c_param.set_acyclic(True)
try_function(generate, ("Test_of_SDFG", c_param))
print "Cyclic SDF generation",
c_param.set_acyclic(False)
SDF = try_function(generate, ("Test_of_SDFG", c_param))
print "SDF Compute repetition vector",
try_function(SDF.compute_repetition_vector, [])
print "Write SDF into sdf3 file",
try_function(write_sdf3_file, (SDF, "SDF.sdf3"))
print "Read SDF into sdf3 file",
try_function(read_sdf3_file, ["SDF.sdf3"])
os.remove("SDF.sdf3")
print "Write SDF into tur file",
try_function(write_tur_file, (SDF, "SDF.tur"))
print "Read SDF into tur file",
try_function(read_tur_file, ["SDF.tur"])
os.remove("SDF.tur")
print "Un-normalized SDF",
try_function(SDF.un_normalized, [])
print "Normalized SDF",
try_function(SDF.normalized, [])

print "SC1 on a SDF",
try_function(SDF.compute_initial_marking, ("SC1", False, None, None))
print "SC2 on a SDF",
try_function(SDF.compute_initial_marking, ("SC2", False, None, None))
print "SC1_k on a SDF",
try_function(SDF.compute_initial_marking, ("SC1", False, None, 1))
print "SC1_MIP on a SDF",
try_function(SDF.compute_initial_marking, ("SC1_MIP", False, None, None))
print "SC1_MIP_k on a SDF",
try_function(SDF.compute_initial_marking, ("SC1_MIP", False, None, 1))
print "Computing period on a SDF",
try_function(SDF.get_period, [])
print "Compute symbolic execution on a SDF",
try_property(SDF.is_dead_lock)

print ""

print "Acyclic SDF generation",
c_param.set_dataflow_type("CSDF")
c_param.set_logging_level(logging.CRITICAL)
c_param.set_multi_graph(True)
c_param.set_reentrant(True)
c_param.set_acyclic(True)
try_function(generate, ("Test_of_CSDFG", c_param))
print "Cyclic CSDF generation",
c_param.set_acyclic(False)
CSDF = try_function(generate, ("Test_of_CSDFG", c_param))
print "CSDF Compute repetition vector",
try_function(CSDF.compute_repetition_vector, [])
print "Write CSDF into sdf3 file",
try_function(write_sdf3_file, (CSDF, "CSDF.sdf3"))
print "Read CSDF into sdf3 file",
try_function(read_sdf3_file, ["CSDF.sdf3"])
os.remove("CSDF.sdf3")
print "Write CSDF into tur file",
try_function(write_tur_file, (CSDF, "CSDF.tur"))
print "Read CSDF into tur file",
try_function(read_tur_file, ["CSDF.tur"])
os.remove("CSDF.tur")
print "Un-normalized CSDF",
try_function(CSDF.un_normalized, [])
print "Normalized CSDF",
try_function(CSDF.normalized, [])

print "SC1 on a CSDF",
try_function(CSDF.compute_initial_marking, ("SC1", False, None, None))
print "SC2 on a CSDF",
try_function(CSDF.compute_initial_marking, ("SC2", False, None, None))
print "SC1_k on a CSDF",
try_function(CSDF.compute_initial_marking, ("SC1", False, None, 1))
print "SC1_MIP on a CSDF",
try_function(CSDF.compute_initial_marking, ("SC1_MIP", False, None, None))
print "SC1_MIP_k on a CSDF",
try_function(CSDF.compute_initial_marking, ("SC1_MIP", False, None, 1))
print "Compute symbolic execution on a CSDF",
try_property(CSDF.is_dead_lock)

print ""

print "Acyclic PCG generation",
c_param.set_dataflow_type("PCG")
c_param.set_logging_level(logging.CRITICAL)
c_param.set_acyclic(True)
c_param.set_multi_graph(True)
c_param.set_reentrant(True)
try_function(generate, ("Test_of_PCG", c_param))
print "Cyclic PCG generation",
c_param.set_acyclic(False)
PCG = try_function(generate, ("Test_of_PCGG", c_param))
print "PCG Compute repetition vector",
try_function(PCG.compute_repetition_vector, [])
print "Write PCG into sdf3 file",
try_function(write_sdf3_file, (PCG, "PCG.sdf3"))
print "Read PCG into sdf3 file",
try_function(read_sdf3_file, ["PCG.sdf3"])
os.remove("PCG.sdf3")
print "Write PCG into tur file",
try_function(write_tur_file, (PCG, "PCG.tur"))
print "Read PCG into tur file",
try_function(read_tur_file, ["PCG.tur"])
os.remove("PCG.tur")
print "Un-normalized PCG",
try_function(PCG.un_normalized, [])
print "Normalized PCG",
try_function(PCG.normalized, [])

print "SC1 on a PCG",
try_function(PCG.compute_initial_marking, ("SC1", False, None, None))
print "SC2 on a PCG",
try_function(PCG.compute_initial_marking, ("SC2", False, None, None))
print "SC1_k on a PCG",
try_function(PCG.compute_initial_marking, ("SC1", False, None, 1))
print "SC1_MIP on a PCG",
try_function(PCG.compute_initial_marking, ("SC1_MIP", False, None, None))
print "SC1_MIP_k on a PCG",
try_function(PCG.compute_initial_marking, ("SC1_MIP", False, None, 1))
print "Compute symbolic execution on a PCG",
try_property(PCG.is_dead_lock)

try:
    os.remove("gurobi.log")
except OSError:
    pass

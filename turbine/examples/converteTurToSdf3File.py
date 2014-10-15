#!/usr/bin/python 
'''
Created on Jul 4, 2014

@author: lesparre
'''

from file_parser.sdf3_parser import write_sdf3_file, read_sdf3_file
from file_parser.turbine_parser import write_tur_file, read_tur_file
from generation.generate import generate
import param.parameters
import sys

if len(sys.argv) != 2 :
    print "This tool need a .tur file as argument and produce a .tur.sdf3 file."
    exit()

filename = sys.argv[1]

# Read Tur file
dataflow = read_tur_file(filename)

# Write the sdf3 file
write_sdf3_file(dataflow, filename + ".sdf3")

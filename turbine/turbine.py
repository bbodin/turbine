#!/usr/bin/python 

import getopt, sys
from param import parameters
from generation import *
from generation.generate import generate
from file_parser.sdf3_parser import  write_sdf3_file 

################# MAIN PARAMETERS AND FUNCTIONS  #######################

main_parameters = parameters.Parameters()


def usage(stub) :
    for (c,l,d,f) in full_parameters :
        if l[len(l)-1] == '=' :
            print "-%s,--%sVALUE%s:%s" % (c,l,' ' * (20 - 5  - len(l)),d)
        else :
            print "-%s,--%s%s: %s" % (c,l,' ' * (20- len(l)),d)
    return True

def set_verbose(level) :
    return False


outputFile = None
def set_output(fileName) :
    global outputFile
    outputFile = fileName
    return True

def set_task(count) :
    global main_parameters
    main_parameters.setNB_TASK(count)
    return True

def set_rv(count) :
    global main_parameters
    main_parameters.setMEAN_RF(count)
    return True

def set_init_phase(phase) :
    global main_parameters
    if len(phase.split(',')) != 2 :
        print "Bad parameter : " + phase
        return False
    main_parameters.setMIN_INIT_PHASE_COUNT(phase.split(',')[0])
    main_parameters.setMAX_INIT_PHASE_COUNT(phase.split(',')[1])
    return True

def set_phase(phase) :
    global main_parameters
    if len(phase.split(',')) != 2 :
        print "Bad parameter : " + phase
        return False
    main_parameters.setMIN_PHASE_COUNT(phase.split(',')[0])
    main_parameters.setMAX_PHASE_COUNT(phase.split(',')[1])
    return True

def set_arc(minmax) :
    global main_parameters
    if len(minmax.split(',')) != 2 :
        print "Bad parameter : " + minmax
        return False
    main_parameters.setMIN_ARCS_COUNT(minmax.split(',')[0])
    main_parameters.setMAX_ARCS_COUNT(minmax.split(',')[1])
    return True

def set_no_self_loop(name) :
    global main_parameters
    main_parameters.setNO_REENTRANT(True)
    return True

def set_solver(name) :
    global main_parameters
    main_parameters.setSOLVER(name)
    return True

full_parameters = [ ('h', "help"           ,"show parameters description", usage) ,
                    ('v', "verbose="       ,"set verbosity level (from 0 to 3)",set_verbose) ,
                    ('o', "output="        ,"set output file (default is stdout)",set_output),
                    ('t', "task="          ,"generation parameter, task",set_task),
                    ('a', "arc="           ,"generation parameter, arc (min,max)",set_arc),
                    ('r', "repetition="    ,"generation parameter, RV",set_rv),
                    ('p', "phase="         ,"generation parameter, phase (min,max)",set_phase),
                    ('i', "init-phase="    ,"add init phases(min,max)",set_init_phase),
                    ('n', "no-self-loop"   ,"dont generate self-loop",set_no_self_loop),
                    ('s', "solver="        ,"solver : SC1,SC2,auto,no ",set_solver)
                  ]

################# MAIN #######################

def main():
    short_opts_w  = "".join([ c + ":"  for  (c,l,d,f) in full_parameters if l[len(l)-1] == '=' ])
    short_opts_wo = "".join([ c  for  (c,l,d,f) in full_parameters if  l[len(l)-1] != '=' ])
 
    try: 
       opts, args = getopt.getopt(sys.argv[1:],short_opts_w + short_opts_wo   , [l for (c,l,d,f) in full_parameters])
    except getopt.GetoptError as err:
        print str(err) # will print something like "option -a not recognized"
        usage(0)
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        see = False
        for (c,l,d,f) in full_parameters :
            if o in ("-"+c,"--"+l) :
                if f(a) == False :
                    print "unsupported param"
                    sys.exit(2)
                see = True
        if not see :
                assert False, "unhandled option '%s', '%s'" % (o,a)

    ################# RUN GENERATOR #######################

    newgraph = generate("autogen",main_parameters)
    write_sdf3_file(newgraph,outputFile)



if __name__ == "__main__":
    main()



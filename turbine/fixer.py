#!/usr/bin/python 

import getopt, sys
from param import parameters
from sdf3.parser import  write_sdf3_file ,  read_sdf3_file 

################# MAIN PARAMETERS AND FUNCTIONS  #######################

main_parameters = parameters.Parameters()
inputFile = None


def usage(stub) :
    for (c,l,d,f) in full_parameters :
        if l[len(l)-1] == '=' :
            print "-%s,--%sVALUE%s:%s" % (c,l,' ' * (20 - 5  - len(l)),d)
        else :
            print "-%s,--%s%s: %s" % (c,l,' ' * (20- len(l)),d)
    return True

def set_verbose(level) :
    return False


def set_input(fileName) :
    global inputFile
    inputFile = fileName
    return True

def set_solver(name) :
    global main_parameters
    main_parameters.setSOLVER(name)
    return True

full_parameters = [ ('h', "help"           ,"show parameters description", usage) ,
                    ('v', "verbose="       ,"set verbosity level (from 0 to 3)",set_verbose) ,
                    ('i', "input="        ,"set input file (default is stdin)",set_input)
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

    if  inputFile != None :           
        newgraph = read_sdf3_file(inputFile)
        write_sdf3_file(newgraph,inputFile)
    else :
        usage(0)
        sys.exit(2)


if __name__ == "__main__":
    main()



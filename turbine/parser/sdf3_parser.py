# -*- coding: utf-8 -*-
from models.graph import Graph
from algorithms.rv import computeRepetitionVector
import sys

import xml.etree.cElementTree as ElementTree  # XML Stuff


# indent ElementTree 
def indent(elem, level=0):    
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
def str_to_int(rate) :
    if rate == '' : return 0
    return float(rate)

def str_to_doubleint(rate) :
    if rate == '' : return (0,0)
    r = rate.split(':')
    if len(r) > 2 : raise BaseException("Bad rate value")
    r.append(r[0])
    return ( int(r[0]) , int(r[0]) )

def split_init_cyclo_durations(durations) :
    initcyclo = durations.split(';')
    if len(initcyclo) > 2 : 
        raise BaseException("Bad rate format")         
    if len(initcyclo) == 0 : 
        raise BaseException("Empty rate format")   
    initcyclo.insert(0,'')
    cyclo = initcyclo.pop()
    init  = initcyclo.pop()
    linit  = [str_to_int(x) for x in init.split(',')]
    lcyclo = [str_to_int(x) for x in cyclo.split(',')]
    if (init == '') : linit = [] # TODO : horrible fix
    return (linit,lcyclo)

def split_init_cyclo_rates(rates) :
    initcyclo = rates.split(';')
    if len(initcyclo) > 2 : 
        raise BaseException("Bad rate format")         
    if len(initcyclo) == 0 : 
        raise BaseException("Empty rate format")   
    initcyclo.insert(0,'')
    cyclo = initcyclo.pop()
    init  = initcyclo.pop()
    linit = init.split(',')
    lcyclo = cyclo.split(',')
    rinit = []
    tinit = []
    if linit[0] != '' : # TODO : very bad
        for x in linit :
            sinit =  str_to_doubleint(x)
            rinit.append(sinit[0])
            tinit.append(sinit[1]) 
    rcyclo = []
    tcyclo = []
    for x in lcyclo :
        scyclo =  str_to_doubleint(x)
        rcyclo.append(scyclo[0])
        tcyclo.append(scyclo[1]) 
    return ((rinit,tinit),(rcyclo,tcyclo))

# -- Sample -- 
# <actorProperties actor='A'>
#  <processor type='cluster_0' default='true'>
#    <executionTime time='1;3,1'/> le point virgule entre les phases d'init et les phases normales
#  </processor>
# </actorProperties>
def parse_sdf3_actorProperties(elem,dataflow,task_ref) :

    for p in elem.getiterator("actorProperties") : # get the first one, don't care default value
        for e in p .getiterator("executionTime") :            
            chaine = e.get("time")
            if chaine != None :
                # 1;3,1 ==>  setPhaseDurationInitList([1]) && setPhaseDurationList([3,1]) 
                (linit,lcyclo) = split_init_cyclo_durations(chaine)
                dataflow.setPhaseCount(task_ref,len(lcyclo))
                dataflow.setPhaseDurationList(task_ref,[int(i) for i in lcyclo])
                dataflow.setPhaseCountInit(task_ref,len(linit))
                dataflow.setPhaseDurationInitList(task_ref,[int(i) for i in linit])

# -- Sample -- 
#<sdfProperties>
#  <actorProperties actor='A'>
#  ...
#  </actorProperties>
#  <actorProperties actor='B'>
#  ...
#  </actorProperties>
#</sdfProperties>
def parse_sdf3_sdfProperties(elem,dataflow) :
    for ap in elem.getiterator("actorProperties") :
        if ap.get("actor") != None :

            dataflow.addTask(ap.get("actor"))
            task_ref = dataflow.getTaskByName(ap.get("actor"))
            parse_sdf3_actorProperties(ap,dataflow,task_ref)

# -- Sample -- 
#<actor name='A' type='a'>
# <port type='in' name='out_channel_2' rate='1;1:3,3'/> init;normal normal:seuil
# <port type='out' name='in_channel_0' rate='3,5'/>
#</actor>
def parse_sdf3_actor (task,dataflow) :
    taskname = task.get("name")      
    task_ref = dataflow.getTaskByName(taskname)
    for port in task.getiterator("port") :
        if port.get("rate") == None :
            raise BaseException()
        if port.get("type") == None :
            raise BaseException()
        if port.get("name") == None :
            raise BaseException()
        portRate = port.get("rate")
        portType = port.get("type")
        portName = port.get("name")
        if portType == "in" :
            for channel in dataflow.getInputArcList(task_ref) :
                if dataflow.getConsPortName(channel) == portName :
                    ((r1,t1),(r2,t2)) = split_init_cyclo_rates(portRate)
                    if len(r1) > 0 : dataflow.setConsInitList(channel,[int(i) for i in r1])
                    if len(t1) > 0 : dataflow.setConsInitThresholdList(channel,[int(i) for i in t1])
                    dataflow.setConsList(channel,[int(i) for i in r2])
                    if len(t2) > 0 and t2 != r2 : dataflow.setConsThresholdList(channel,[int(i) for i in t2])
        if portType == "out" :
            for channel in dataflow.getOutputArcList(task_ref) :
                if dataflow.getProdPortName(channel) == portName :
                    ((r1,t1),(r2,t2)) = split_init_cyclo_rates(portRate)
                    if len(r1) > 0 : dataflow.setProdInitList(channel,[int(i) for i in r1])
                    dataflow.setProdList(channel,[int(i) for i in r2])

# -- Sample -- 
#<sdf name='Cyclic' type='Cyclic'>
#<actor name='A' type='a'>
#</actor>
#<channel name='channel_0' srcActor='A' srcPort='in_channel_0' dstActor='B' dstPort='out_channel_0' size='1' initialTokens='0'/>
#</sdf>
def parse_sdf3_sdf (elem,dataflow) :

    # Check input value
    if elem.tag != "sdf" :   
        if elem.tag != "csdf" :
            raise BaseException()

    # Read channels (all buffer are created, with portnames, preload and tokensize)
    for channel in elem.getiterator("channel"):
        source = dataflow.getTaskByName(channel.get("srcActor"))
        target = dataflow.getTaskByName(channel.get("dstActor"))
        channel_ref = dataflow.addArc(source,target)
#         if channel.get("name") != None :
#             dataflow.setArcName(channel_ref,channel.get("name"))
        if channel.get("initialTokens") != None : 
            dataflow.setInitialMarking(channel_ref,int(channel.get("initialTokens")))
        if channel.get("size") != None : 
            dataflow.setTokenSize(channel_ref,int(channel.get("size")))
        if channel.get("srcPort") == None : 
            raise BaseException()
        if channel.get("dstPort") == None : 
            raise BaseException()
        dataflow.setProdPortName(channel_ref,channel.get("srcPort")) 
        dataflow.setConsPortName(channel_ref,channel.get("dstPort")) 
      
    # Read rates from task list
    for task in elem.getiterator("actor"):
        parse_sdf3_actor (task,dataflow)

# -- Sample --  
#<applicationGraph name='Cyclic'>
#<sdf name='Cyclic' type='Cyclic'>
#</sdf>
#<sdfProperties>
#</sdfProperties>
#</applicationGraph>
def parse_sdf3_applicationGraph (elem,dataflow) :

    # Check input value
    if elem.tag != "applicationGraph" :
        raise BaseException()

    # Get name
    if elem.get("name") != None :
        dataflow.setName(elem.get("name"))

    # Read sdfProperties node (to do before sdf to resolve phase count and task)
    pdone = False
    for child in elem:
        if child.tag == "sdfProperties" :
            parse_sdf3_sdfProperties(child,dataflow)
            pdone = True
        else :
            if child.tag == "csdfProperties" :
                parse_sdf3_sdfProperties(child,dataflow)
                pdone = True

    if pdone == False :
        raise BaseException("no graph properties found")

    # Read sdf node first
    gdone = False
    for child in elem:
        if child.tag == "sdf" :
            parse_sdf3_sdf(child,dataflow)
            gdone=True
        else :
            if  child.tag == "csdf" :
                parse_sdf3_sdf(child,dataflow)
                gdone=True

    if gdone == False :
        raise BaseException("no graph found")

# -- Sample --
#<?xml version="1.0" encoding="UTF-8"?>
#<sdf3 type="sdf" version="1.0"
#    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#    xsi:noNamespaceSchemaLocation="http://www.es.ele.tue.nl/sdf3/xsd/sdf3-sdf.xsd">
#<applicationGraph name='Cyclic'>
#</applicationGraph>
#</sdf3>
def parse_sdf3_node (root) : 

    # Check input value
    if root.tag != "sdf3" :
        raise BaseException()
    if root.get("type") == None :
        raise BaseException()

    # Return value
    dataflow = None
   
    if  root.get("type") == "sdf" :
        dataflow = Graph("sdf")
    else :
        if  root.get("type") == "csdf" :
            dataflow = Graph("csdf")
        else :
            raise ValueError
    for applicationGraph in root:
        parse_sdf3_applicationGraph(applicationGraph,dataflow)

    return dataflow

def gen_sdf3_sdfProperties (dataflow) :
    sdfp = ElementTree.Element("sdfProperties")  
    for task in dataflow.getTaskList() :
        exectime = ElementTree.Element("executionTime") 
        exectime.set("time",dataflow.getTaskDurationStr(task))
        processor = ElementTree.Element("processor") 
        processor.set("type",'cluster_0')
        processor.set("default",'true')
        processor.append(exectime)
        t = ElementTree.Element("actorProperties")
        t.set("actor",str(dataflow.getTaskName(task)))
        t.append(processor)
        sdfp.append(t)
    return sdfp

# <port type='in' name='out_channel_2' rate='6'/>
def gen_sdf3_in_port(dataflow, arc) :
    port = ElementTree.Element("port")  
    port.set("type","in")
    port.set("name",str(dataflow.getConsPortName(arc)))
    port.set("rate",str(dataflow.getConsStr(arc)))
    return port

# <port type='out' name='out_channel_2' rate='6'/>
def gen_sdf3_out_port(dataflow ,arc) :
    port = ElementTree.Element("port")  
    port.set("type","out")
    port.set("name",str(dataflow.getProdPortName(arc)))
    port.set("rate",str(dataflow.getProdStr(arc)))
    return port

def gen_sdf3_sdf (dataflow) :
    sdf = ElementTree.Element("sdf")  
    sdf.set("name",dataflow.getName())   
    sdf.set("type",dataflow.getName())
    for task in dataflow.getTaskList() :
        t = ElementTree.Element("actor")  
        t.set("name",dataflow.getTaskName(task))   
        t.set("type","actor")
        for c in dataflow.getInputArcList(task) :
            t.append( gen_sdf3_in_port(dataflow,c))
        for c in dataflow.getOutputArcList(task) :
            t.append( gen_sdf3_out_port(dataflow,c))
        sdf.append(t)
    #<channel name='channel_0' srcActor='A' srcPort='in_channel_0'
    #... dstActor='B' dstPort='out_0' size='1' initialTokens='0'/>
    for channel in dataflow.getArcList() :
        c = ElementTree.Element("channel")  
        c.set("name",dataflow.getArcName(channel))
        c.set("srcActor",str(dataflow.getTaskName(dataflow.getSource(channel))))
        c.set("srcPort",str(dataflow.getProdPortName(channel)))
        c.set("dstActor",str(dataflow.getTaskName(dataflow.getTarget(channel))))
        c.set("dstPort",str(dataflow.getConsPortName(channel)))
        c.set("size",str(dataflow.getTokenSize(channel)))
        c.set("initialTokens",str(dataflow.getInitialMarking(channel)))
        sdf.append(c)
    return sdf

def gen_sdf3_applicationGraph (dataflow) :
    ag = ElementTree.Element("applicationGraph")
    ag.set("name",dataflow.getName())
    ag.append(gen_sdf3_sdf(dataflow))
    ag.append(gen_sdf3_sdfProperties(dataflow))
    return ag

def gen_sdf3_node (dataflow) : 
    root = ElementTree.Element("sdf3")
    root.set("type","csdf") # TODO Gerer les types
    root.set("version","1.0")
    root.set("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation","http://www.es.ele.tue.nl/sdf3/xsd/sdf3-csdf.xsd")
    root.append(gen_sdf3_applicationGraph(dataflow))
    return root

def read_sdf3_file (fileName) :
    xmltree = ElementTree.parse(fileName)
    graph = parse_sdf3_node(xmltree.getroot())
    computeRepetitionVector(graph)
    return graph

def write_sdf3_file(dataflow,fileName = None) :
    xmltree = gen_sdf3_node(dataflow)
    indent(xmltree)
    mon_fichier = sys.stdout
    if fileName != None :
        mon_fichier = open(fileName, "w")
    mon_fichier.write(ElementTree.tostring(xmltree,encoding="UTF-8"))#
    mon_fichier.close()

# -*- coding: utf-8 -*-
import sys
import xml.etree.cElementTree as ElementTree  # XML Stuff

from Turbine.algorithms.rv import compute_rep_vect
from Turbine.graph_classe.pcg import PCG
from Turbine.graph_classe.csdf import CSDF
from Turbine.graph_classe.sdf import SDF


# indent ElementTree
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def str_to_int(rate):
    if rate == '':
        return 0
    return float(rate)


def str_to_doubleint(rate):
    if rate == '':
        return 0, 0
    r = rate.split(':')
    if len(r) > 2:
        raise BaseException("Bad rate value")
    r.append(r[0])
    return int(r[0]), int(r[0])


def split_init_cyclo_durations(durations):
    initcyclo = durations.split(';')
    if len(initcyclo) > 2:
        raise BaseException("Bad rate format")         
    if len(initcyclo) == 0:
        raise BaseException("Empty rate format")   
    initcyclo.insert(0, '')
    cyclo = initcyclo.pop()
    init = initcyclo.pop()
    linit = [str_to_int(x) for x in init.split(',')]
    lcyclo = [str_to_int(x) for x in cyclo.split(',')]
    if init == '':
        linit = []  # TODO: horrible fix
    return linit, lcyclo


def split_init_cyclo_rates(rates):
    initcyclo = rates.split(';')

    if len(initcyclo) > 2:
        raise BaseException("Bad rate format")         
    if len(initcyclo) == 0:
        raise BaseException("Empty rate format")

    cyclo = initcyclo.pop()
    if not initcyclo == []:
        init = initcyclo.pop()
        linit = init.split(',')
    else:
        linit = []
    lcyclo = cyclo.split(',')
    rinit = []
    tinit = []
    for value in linit:
        if len(value.split(":")) == 1:
            rinit.append(int(value))
            tinit.append(int(value))
        else:
            rate, threshold = value.split(":")
            rinit.append(int(rate))
            tinit.append(int(threshold))
    rcyclo = []
    tcyclo = []
    for value in lcyclo:
        if len(value.split(":")) == 1:
            rcyclo.append(int(value))
            tcyclo.append(int(value))
        else:
            rate, threshold = value.split(":")
            rcyclo.append(int(rate))
            tcyclo.append(int(threshold))
    return (rinit, tinit), (rcyclo, tcyclo)


# -- Sample -- 
# <actorProperties actor='A'>
#  <processor type='cluster_0' default='true'>
#    <executionTime time='1;3,1'/> le point virgule entre les phases d'init et les phases normales
#  </processor>
# </actorProperties>
def parse_sdf3_actor_properties(elem, dataflow, task_ref):
    for p in elem.getiterator("actorProperties"):  # get the first one, don't care default value
        for e in p .getiterator("executionTime"):
            chaine = e.get("time")
            if chaine is not None:
                # 1;3,1 ==>  setPhaseDurationInitList([1]) && setPhaseDurationList([3,1]) 
                (linit, lcyclo) = split_init_cyclo_durations(chaine)
                if isinstance(dataflow, SDF):
                    dataflow.set_task_duration(task_ref, int(lcyclo[0]))
                if isinstance(dataflow, CSDF):
                    dataflow.set_phase_count(task_ref, len(lcyclo))
                    dataflow.set_phase_duration_list(task_ref, [int(i) for i in lcyclo])
                if isinstance(dataflow, PCG):
                    dataflow.set_ini_phase_count(task_ref, len(linit))
                    dataflow.set_ini_phase_duration_list(task_ref, [int(i) for i in linit])


# -- Sample -- 
# <sdfProperties>
#  <actorProperties actor='A'>
#  ...
#  </actorProperties>
#  <actorProperties actor='B'>
#  ...
#  </actorProperties>
# </sdfProperties>
def parse_sdf3_sdf_properties(elem, dataflow):
    for ap in elem.getiterator("actorProperties"):
        if ap.get("actor") is not None:
            dataflow.add_task(ap.get("actor"))
            task_ref = dataflow.get_task_by_name(ap.get("actor"))
            parse_sdf3_actor_properties(ap, dataflow, task_ref)


# -- Sample -- 
# <actor name='A' type='a'>
# <port type='in' name='out_channel_2' rate='1;1:3,3'/> init;normal normal:seuil
# <port type='out' name='in_channel_0' rate='3,5'/>
# </actor>
def parse_sdf3_actor(task, dataflow):
    taskname = task.get("name")      
    task_ref = dataflow.get_task_by_name(taskname)
    for port in task.getiterator("port"):
        if port.get("rate") is None:
            raise BaseException()
        if port.get("type") is None:
            raise BaseException()
        if port.get("name") is None:
            raise BaseException()
        port_rate = port.get("rate")
        port_type = port.get("type")
        port_name = port.get("name")
        if port_type == "in":
            for channel in dataflow.get_arc_list(target=task_ref):
                if dataflow.get_cons_port_name(channel) == port_name:
                    ((r1, t1), (r2, t2)) = split_init_cyclo_rates(port_rate)
                    if isinstance(dataflow, SDF):
                        dataflow.set_cons_rate(channel, r2[0])
                    if isinstance(dataflow, CSDF):
                        dataflow.set_cons_rate_list(channel, [int(i) for i in r2])
                    if isinstance(dataflow, PCG) and len(r1) > 0:
                        dataflow.set_ini_cons_rate_list(channel, [int(i) for i in r1])
                    if isinstance(dataflow, PCG) and len(t1) > 0:
                        dataflow.set_ini_threshold_list(channel, [int(i) for i in t1])
                    if isinstance(dataflow, PCG) and len(t2) > 0 and t2 != r2:
                        dataflow.set_threshold_list(channel, [int(i) for i in t2])
        if port_type == "out":
            for channel in dataflow.get_arc_list(source=task_ref):
                if dataflow.get_prod_port_name(channel) == port_name:
                    ((r1, t1), (r2, t2)) = split_init_cyclo_rates(port_rate)
                    if isinstance(dataflow, SDF):
                        dataflow.set_prod_rate(channel, r2[0])
                    if isinstance(dataflow, CSDF):
                        dataflow.set_prod_rate_list(channel, [int(i) for i in r2])
                    if isinstance(dataflow, PCG) and len(r1) > 0:
                        dataflow.set_ini_prod_rate_list(channel, [int(i) for i in r1])


# -- Sample -- 
# <sdf name='Cyclic' type='Cyclic'>
# <actor name='A' type='a'>
# </actor>
# <channel name='channel_0' srcActor='A' srcPort='in_channel_0'
# dstActor='B' dstPort='out_channel_0' size='1' initialTokens='0'/>
# </sdf>
def parse_sdf3_sdf(elem, dataflow):

    # Check input value
    if elem.tag != "sdf":
        if elem.tag != "csdf":
            raise BaseException()

    # Read channels (all bds are created, with portnames, preload and tokensize)
    for channel in elem.getiterator("channel"):
        source = dataflow.get_task_by_name(channel.get("srcActor"))
        target = dataflow.get_task_by_name(channel.get("dstActor"))
        channel_ref = dataflow.add_arc(source, target)
        if channel.get("name") is not None:
            dataflow.set_arc_name(channel_ref, channel.get("name"))
        if channel.get("initialTokens") is not None:
            dataflow.set_initial_marking(channel_ref, int(channel.get("initialTokens")))
        if channel.get("size") is not None:
            dataflow.set_token_size(channel_ref, int(channel.get("size")))
        if channel.get("srcPort") is None:
            raise BaseException()
        if channel.get("dstPort") is None:
            raise BaseException()
        dataflow.set_prod_port_name(channel_ref, channel.get("srcPort"))
        dataflow.set_cons_port_name(channel_ref, channel.get("dstPort"))
      
    # Read rates from task list
    for task in elem.getiterator("actor"):
        parse_sdf3_actor(task, dataflow)


# -- Sample --  
# <applicationGraph name='Cyclic'>
# <sdf name='Cyclic' type='Cyclic'>
# </sdf>
# <sdfProperties>
# </sdfProperties>
# </applicationGraph>
def parse_sdf3_application_graph(elem, dataflow):

    # Check input value
    if elem.tag != "applicationGraph":
        raise BaseException()

    # Get name
    if elem.get("name") is None:
        dataflow.setName(elem.get("name"))

    # Read sdfProperties node (to do before sdf to resolve phase count and task)
    pdone = False
    for child in elem:
        if child.tag == "sdfProperties" or child.tag == "csdfProperties":
            parse_sdf3_sdf_properties(child, dataflow)
            pdone = True

    if not pdone:
        raise BaseException("no graph properties found")

    # Read sdf node first
    gdone = False
    for child in elem:
        if child.tag == "sdf":
            parse_sdf3_sdf(child, dataflow)
            gdone = True
        elif child.tag == "csdf":
            parse_sdf3_sdf(child, dataflow)
            gdone = True
        elif child.tag == "pcg":
            parse_sdf3_sdf(child, dataflow)
            gdone = True

    if not gdone:
        raise BaseException("no graph found")


# -- Sample --
# <?xml version="1.0" encoding="UTF-8"?>
# <sdf3 type="sdf" version="1.0"
#    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#    xsi:noNamespaceSchemaLocation="http://www.es.ele.tue.nl/sdf3/xsd/sdf3-sdf.xsd">
# <applicationGraph name='Cyclic'>
# </applicationGraph>
# </sdf3>
def parse_sdf3_node(root, name):

    # Check input value
    if root.tag != "sdf3":
        raise BaseException()
    if root.get("type") is None:
        raise BaseException()
    if root.get("type") == "sdf":
        dataflow = SDF(name)
    elif root.get("type") == "csdf":
        dataflow = CSDF(name)
    elif root.get("type") == "pcg":
        dataflow = PCG(name)
    else:
        raise ValueError
    for applicationGraph in root:
        parse_sdf3_application_graph(applicationGraph, dataflow)

    return dataflow

def gen_sdf3_csdf_properties (dataflow) :
    csdfp = ElementTree.Element("csdfProperties")  
    for task in dataflow.get_task_list():
        exetime = ElementTree.Element("executionTime")
        exetime.set("time", dataflow.get_duration_str(task))
        processor = ElementTree.Element("processor")
        processor.set("type", 'cluster_0')
        processor.set("default", 'true')
        processor.append(exetime)
        t = ElementTree.Element("actorProperties")
        t.set("actor", str(dataflow.get_task_name(task)))
        t.append(processor)
        csdfp.append(t)
    return csdfp

def gen_sdf3_sdf_properties(dataflow):
    sdfp = ElementTree.Element("sdfProperties")  
    for task in dataflow.get_task_list():
        exetime = ElementTree.Element("executionTime")
        exetime.set("time", dataflow.get_duration_str(task))
        processor = ElementTree.Element("processor")
        processor.set("type", 'cluster_0')
        processor.set("default", 'true')
        processor.append(exetime)
        t = ElementTree.Element("actorProperties")
        t.set("actor", str(dataflow.get_task_name(task)))
        t.append(processor)
        sdfp.append(t)
    return sdfp


# <port type='in' name='out_channel_2' rate='6'/>
def gen_sdf3_in_port(dataflow, arc):
    port = ElementTree.Element("port")  
    port.set("type", "in")
    port.set("name", str(dataflow.get_cons_port_name(arc)))
    port.set("rate", str(dataflow.get_cons_str(arc)))
    return port


# <port type='out' name='out_channel_2' rate='6'/>
def gen_sdf3_out_port(dataflow, arc):
    port = ElementTree.Element("port")  
    port.set("type", "out")
    port.set("name", str(dataflow.get_prod_port_name(arc)))
    port.set("rate", str(dataflow.get_prod_str(arc)))
    return port

def gen_sdf3_csdf (dataflow) :
    csdf = ElementTree.Element("csdf")  
    csdf.set("name", dataflow.get_name())
    csdf.set("type", dataflow.get_name())
    for task in dataflow.get_task_list():
        t = ElementTree.Element("actor")  
        t.set("name", dataflow.get_task_name(task))
        t.set("type", "actor")
        for c in dataflow.get_arc_list(target=task):
            t.append(gen_sdf3_in_port(dataflow, c))
        for c in dataflow.get_arc_list(source=task):
            t.append(gen_sdf3_out_port(dataflow, c))
        csdf.append(t)
    # <channel name='channel_0' srcActor='A' srcPort='in_channel_0'
    # ... dstActor='B' dstPort='out_0' size='1' initialTokens='0'/>
    for channel in dataflow.get_arc_list():
        c = ElementTree.Element("channel")  
        c.set("name", dataflow.get_arc_name(channel))
        c.set("srcActor", str(dataflow.get_task_name(dataflow.get_source(channel))))
        c.set("srcPort", str(dataflow.get_prod_port_name(channel)))
        c.set("dstActor", str(dataflow.get_task_name(dataflow.get_target(channel))))
        c.set("dstPort", str(dataflow.get_cons_port_name(channel)))
        c.set("size", str(dataflow.get_token_size(channel)))
        c.set("initialTokens", str(dataflow.get_initial_marking(channel)))
        csdf.append(c)
    return csdf


def gen_sdf3_sdf(dataflow):
    sdf = ElementTree.Element("sdf")  
    sdf.set("name", dataflow.get_name())
    sdf.set("type", dataflow.get_name())
    for task in dataflow.get_task_list():
        t = ElementTree.Element("actor")  
        t.set("name", dataflow.get_task_name(task))
        t.set("type", "actor")
        for c in dataflow.get_arc_list(target=task):
            t.append(gen_sdf3_in_port(dataflow, c))
        for c in dataflow.get_arc_list(source=task):
            t.append(gen_sdf3_out_port(dataflow, c))
        sdf.append(t)
    # <channel name='channel_0' srcActor='A' srcPort='in_channel_0'
    # ... dstActor='B' dstPort='out_0' size='1' initialTokens='0'/>
    for channel in dataflow.get_arc_list():
        c = ElementTree.Element("channel")  
        c.set("name", dataflow.get_arc_name(channel))
        c.set("srcActor", str(dataflow.get_task_name(dataflow.get_source(channel))))
        c.set("srcPort", str(dataflow.get_prod_port_name(channel)))
        c.set("dstActor", str(dataflow.get_task_name(dataflow.get_target(channel))))
        c.set("dstPort", str(dataflow.get_cons_port_name(channel)))
        c.set("size", str(dataflow.get_token_size(channel)))
        c.set("initialTokens", str(dataflow.get_initial_marking(channel)))
        sdf.append(c)
    return sdf


def gen_sdf3_node(dataflow):
    root = ElementTree.Element("sdf3")
    if isinstance(dataflow, SDF):
        root.set("type", "sdf")
    if isinstance(dataflow, CSDF) and not isinstance(dataflow, PCG):
        root.set("type", "csdf")
    if isinstance(dataflow, PCG):
        root.set("type", "pcg")
    root.set("version", "1.0")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation", "http://www.es.ele.tue.nl/sdf3/xsd/sdf3-csdf.xsd")

    ag = ElementTree.Element("applicationGraph")
    ag.set("name", dataflow.get_name())
    if isinstance(dataflow, SDF):
        ag.append(gen_sdf3_sdf(dataflow))
        ag.append(gen_sdf3_sdf_properties(dataflow))
    else :
        ag.append(gen_sdf3_csdf(dataflow))
        ag.append(gen_sdf3_csdf_properties(dataflow))
    root.append(ag)

    return root


def read_sdf3_file(filename):
    xmltree = ElementTree.parse(filename)
    name = filename.split("/")[-1]
    graph = parse_sdf3_node(xmltree.getroot(), name)
    compute_rep_vect(graph)
    return graph


def write_sdf3_file(dataflow, filename=None):
    xmltree = gen_sdf3_node(dataflow)
    indent(xmltree)
    w_file = sys.stdout
    if filename is not None:
        w_file = open(filename, "w")
    w_file.write(ElementTree.tostring(xmltree, encoding="UTF-8"))
    w_file.close()

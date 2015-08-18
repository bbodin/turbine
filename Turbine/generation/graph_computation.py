from random import *
import logging

from Turbine.graph_classe.csdf import CSDF
from Turbine.graph_classe.pcg import PCG
from Turbine.graph_classe.sdf import SDF


def __get_random_task(graph):
    return graph.get_task_list()[randint(0, graph.get_task_count() - 1)]


########################################################################
#                           generate graph                             #
########################################################################
def generate_dataflow(dataflow_name, c_param):
    """Step 1
    """
    if c_param.get_dataflow_type() == "SDF":
        dataflow = SDF(dataflow_name)
    if c_param.get_dataflow_type() == "CSDF":
        dataflow = CSDF(dataflow_name)
    if c_param.get_dataflow_type() == "PCG":
        dataflow = PCG(dataflow_name)
    __generate_connex_graph(dataflow, c_param)  # Generate a Tree graph
    __generate_arcs_parceled(dataflow, c_param, 2, 5, 0.1, 0.5)  # Add arcs to the Tree graph
    return dataflow


def __generate_connex_graph(graph, c_param):
    logging.info("Generate connex graph")
    graph.add_task()
    for i in xrange(1, c_param.get_nb_task()):
        task = graph.add_task()
        random_task = __get_random_task(graph)
        while random_task == task:
            random_task = __get_random_task(graph)
        if randint(0, 1):
            graph.add_arc(task, random_task)
        else:
            graph.add_arc(random_task, task)
        if graph.get_task_count() > 1000 and i % 1000 == 0:
            logging.info(str(i) + "/" + str(c_param.get_nb_task()) + " tasks generate.")


def __generate_arcs(graph, c_param):
    logging.info("Generate more arcs")
    
    in_task = []
    out_task = []

    # We begin with the generation of in channel
    for i in xrange(0, graph.get_task_count()):
        arcs_in_count = randint(c_param.get_min_arcs_count(), c_param.get_max_arcs_count())

        # random number of arcs for each tasks - 1 because each task already have one arc.
        if graph.get_input_degree(i) > 0:
            arcs_in_count -= 1
        in_task += [i] * arcs_in_count
    shuffle(in_task)

    # Generation of out channel depending of reentrant option
    if not c_param.is_reentrant():
        for i in xrange(0, graph.get_task_count()):
            arcs_out_count = randint(c_param.get_min_arcs_count(), c_param.get_max_arcs_count())
            # random number of arcs for each tasks - 1 because each task already have one arc.
            if graph.get_output_degree(i) > 0:
                arcs_out_count -= 1
            out_task += [i] * arcs_out_count
        shuffle(out_task)
    else:  # NoReentrant part
        for elem in in_task:
            out = randint(0, graph.get_task_count() - 1)
            while out == elem:
                out = randint(0, graph.get_task_count() - 1)
            out_task += [out]

    nb_tot_arcs = min(len(in_task), len(out_task))
    for i in xrange(0, nb_tot_arcs):
        graph.add_arc(out_task[i], in_task[i])
        if graph.get_task_count() > 1000 and i % 1000 == 0:
            logging.info(str((i + 1) + graph.get_task_count()) +
                         "/" + str(nb_tot_arcs + graph.get_task_count()) + " arcs added.")


def __generate_arcs_parceled(graph, c_param, min_parcel, max_parcel, min_task, max_task):
    logging.info("Generate more arcs")
    
    in_task = []
    out_task = []
    parcel_task_num = []
    parcel_num = randint(min_parcel, max_parcel)

    min_parcel_task_count = int(graph.get_task_count()*min_task)
    max_parcel_task_count = int(graph.get_task_count()*max_task)
    for i in xrange(parcel_num):
        in_task.append([])
        out_task.append([])
        
        parcel_task_num.append(randint(min_parcel_task_count, max_parcel_task_count))

    parcel_task_num[parcel_num-1] = graph.get_task_count()
    for i in xrange(parcel_num-1):
        parcel_task_num[parcel_num-1] -= parcel_task_num[i]

    task_parcel = []
    parcel_full = 0
    # We begin with the generation of in channel
    for i in xrange(0, graph.get_task_count()):
        arcs_in_count = randint(c_param.get_min_arcs_count(), c_param.get_max_arcs_count())

        # random number of arcs for each tasks - 1 because each task already have one arc.
        if graph.get_input_degree(i) > 0:
            arcs_in_count -= 1
        parcel = randint(0, parcel_num-parcel_full-1)
        task_parcel.append(parcel)
        in_task[parcel] += [i] * arcs_in_count
        parcel_task_num[parcel] -= 1
        if parcel_task_num[parcel] == 0:
            parcel_full += 1
            if parcel != parcel_num-parcel_full:
                temp = in_task[parcel]
                in_task[parcel] = in_task[parcel_num-parcel_full]
                in_task[parcel_num-parcel_full] = temp
                parcel_task_num[parcel] = parcel_task_num[parcel_num-parcel_full]
                parcel_task_num[parcel_num-parcel_full] = 0
                for task in xrange(0, i+1):  # TODO : non opti
                    if task_parcel[task] == parcel:
                        task_parcel[task] = parcel_num-parcel_full

    # Generation of out channel
    for i in xrange(0, graph.get_task_count()):
        arcs_out_count = randint(c_param.get_min_arcs_count(), c_param.get_max_arcs_count())
        # random number of arcs for each tasks - 1 because each task already have one arc.
        if graph.get_output_degree(i) > 0:
            arcs_out_count -= 1
        out_task[task_parcel[i]] += [i] * arcs_out_count

    for i in xrange(0, parcel_num):
        shuffle(in_task[i])
        shuffle(out_task[i])

    for parcel in xrange(0, parcel_num):
        nb_tot_arcs = min(len(in_task[parcel]), len(out_task[parcel]))
        for i in xrange(0, nb_tot_arcs):
            graph.add_arc(out_task[parcel][i], in_task[parcel][i])
            if graph.get_task_count() > 1000 and i % 1000 == 0:
                logging.info(str((i + 1) + graph.get_task_count()) +
                             "/" + str(nb_tot_arcs + graph.get_task_count()) + " arcs added.")

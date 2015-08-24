from random import *
import logging
import math

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
    if c_param.is_acyclic():
        path = __generate_connex_dag(dataflow, c_param)  # Generate a simple connex directed acyclic graph
        __generate_arcs_dag(dataflow, c_param, path)  # Add arcs
    else:
        __generate_connex_graph(dataflow, c_param)  # Generate simple connex graph
        __generate_arcs(dataflow, c_param)  # Add arcs
    return dataflow


def __generate_connex_graph(dataflow, c_param):
    logging.info("Generate connex graph")
    dataflow.add_task()
    for i in xrange(1, c_param.get_nb_task()):
        task = dataflow.add_task()
        random_task = __get_random_task(dataflow)
        while random_task == task:
            random_task = __get_random_task(dataflow)
        if randint(0, 1):
            dataflow.add_arc(task, random_task)
        else:
            dataflow.add_arc(random_task, task)
        if dataflow.get_task_count() > 1000 and i % 1000 == 0:
            logging.info(str(i) + "/" + str(c_param.get_nb_task()) + " tasks generate.")


def __generate_arcs(dataflow, c_param):
    logging.info("Generate more arcs")

    in_task = []
    out_task = []

    # We begin with the generation of in channel
    for i in xrange(0, dataflow.get_task_count()):
        arcs_in_count = randint(c_param.get_min_arcs_count(), c_param.get_max_arcs_count())

        # random number of arcs for each tasks - 1 because each task already have one arc.
        if dataflow.get_input_degree(i) > 0:
            arcs_in_count -= 1
        in_task += [i] * arcs_in_count
    shuffle(in_task)

    # Generation of out channel depending of reentrant option
    if not c_param.is_reentrant():
        for i in xrange(0, dataflow.get_task_count()):
            arcs_out_count = randint(c_param.get_min_arcs_count(), c_param.get_max_arcs_count())
            # random number of arcs for each tasks - 1 because each task already have one arc.
            if dataflow.get_output_degree(i) > 0:
                arcs_out_count -= 1
            out_task += [i] * arcs_out_count
        shuffle(out_task)
    else:  # NoReentrant part
        for elem in in_task:
            out = randint(0, dataflow.get_task_count() - 1)
            while out == elem:
                out = randint(0, dataflow.get_task_count() - 1)
            out_task += [out]

    nb_tot_arcs = min(len(in_task), len(out_task))
    for i in xrange(0, nb_tot_arcs):
        dataflow.add_arc(out_task[i], in_task[i])
        if dataflow.get_task_count() > 1000 and i % 1000 == 0:
            logging.info(str(dataflow.get_arc_count()) +
                         "/" + str(nb_tot_arcs + dataflow.get_task_count()) + " arcs added.")


def __generate_connex_dag(dataflow, c_param):
    logging.info("Generate connex directed acyclic graph")
    # First generate a path graph with x nodes and x-1 arcs
    if c_param.get_nb_task() < 10:
        path_nodes_nb = randint(1, int(math.ceil(c_param.get_nb_task() / 2.0)))
    else:
        path_nodes_nb = int(c_param.get_nb_task() / randint(2, int(c_param.get_nb_task() / 2)))

    path = []
    for _ in xrange(path_nodes_nb):
        path.append([])

    task = dataflow.add_task()
    path[0].append(task)
    for i in xrange(1, path_nodes_nb):
        next_task = dataflow.add_task()
        dataflow.add_arc(task, next_task)
        task = next_task
        path[i].append(task)
    if c_param.get_nb_task() - path_nodes_nb > 0:
        for i in xrange(c_param.get_nb_task() - path_nodes_nb):
            path_rank = randint(0, path_nodes_nb - 1)
            task = dataflow.add_task()
            path[path_rank].append(task)
            __add_random_dag_arc(dataflow, task, path_rank, path)
    return path


def __generate_arcs_dag(dataflow, c_param, path):
    logging.info("Generate more arcs")
    nb_arc_min = c_param.get_min_arcs_count() if c_param.get_min_arcs_count() == 0 else c_param.get_min_arcs_count() - 1
    nb_arc_max = c_param.get_max_arcs_count() if c_param.get_max_arcs_count() == 0 else c_param.get_max_arcs_count() - 1

    arc_nb = [randint(nb_arc_min, nb_arc_max) for _ in xrange(dataflow.get_task_count())]
    nb_tot_arcs = sum(arc_nb)

    added_arc_nb = 0
    task_nb = 0
    for path_rank in xrange(len(path)):
        for task in path[path_rank]:
            for _ in xrange(arc_nb[task_nb]):
                __add_random_dag_arc(dataflow, task, path_rank, path)
                added_arc_nb += 1
                logging.info(str((added_arc_nb + 1) + dataflow.get_task_count()) +
                             "/" + str(nb_tot_arcs + dataflow.get_task_count()) + " arcs added.")


def __add_random_dag_arc(dataflow, task, task_rank, path):
    path_nodes_nb = len(path)
    if task_rank == path_nodes_nb - 1 or (task_rank != 0 and randint(0, 1) == 0):
        random_rank = randint(0, task_rank - 1)
    else:
        random_rank = randint(task_rank + 1, path_nodes_nb - 1)

    random_task = path[random_rank][randint(0, len(path[random_rank])-1)]

    if task_rank > random_rank:
        dataflow.add_arc(random_task, task)
    else:
        dataflow.add_arc(task, random_task)

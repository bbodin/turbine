from random import *
import logging

from Turbine.graph_classe.csdf import CSDF
from Turbine.graph_classe.pcg import PCG
from Turbine.graph_classe.sdf import SDF


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
        task_rank, task_degree = __generate_connex_dag(dataflow, c_param)  # Generate a connected acyclic graph
        __generate_arcs_dag(dataflow, c_param, task_rank, task_degree)  # Add arcs such as the graph stay acyclic
    else:
        task_degree = __generate_connex_graph(dataflow, c_param)  # Generate simple connected graph
        __generate_arcs(dataflow, c_param, task_degree)  # Add arcs
    return dataflow


def __generate_connex_graph(dataflow, c_param):
    logging.info("Generate connex graph")
    task_degree = [0] * c_param.get_nb_task()
    potential_emergency_task = set()
    emergency_task = set()
    for task in xrange(c_param.get_nb_task()):  # Compute degree wanted for each task
        task_degree[task] = randint(c_param.get_min_task_degree(), c_param.get_max_task_degree())
        if task_degree[task] < c_param.get_max_task_degree():
            potential_emergency_task.add(task)
    task_degree_non_null = set([])
    task = dataflow.add_task()
    __try_add_emergency_task(task, potential_emergency_task, emergency_task)
    task_degree_non_null.add(task)
    for i in xrange(1, c_param.get_nb_task()):
        try:
            random_task = sample(task_degree_non_null, 1)[0]
        except ValueError:
            random_task = sample(emergency_task, 1)[0]
            emergency_task.remove(random_task)
        task = dataflow.add_task()
        __try_add_emergency_task(task, potential_emergency_task, emergency_task)
        task_degree_non_null.add(task)
        if randint(0, 1):
            dataflow.add_arc(task, random_task)
        else:
            dataflow.add_arc(random_task, task)
        for t in [task, random_task]:
            task_degree[t] -= 1
            if task_degree[t] <= 0:
                task_degree_non_null.discard(t)

        if dataflow.get_task_count() > 1000 and i % 1000 == 0:
            logging.info(str(i) + "/" + str(c_param.get_nb_task()) + " tasks generate.")
    return task_degree


def __generate_arcs(dataflow, c_param, task_degree):
    logging.info("Generate more arcs")

    nb_tot_arcs = dataflow.get_task_count() - 1 + sum(task_degree)
    arc_count = dataflow.get_task_count() - 1
    task_degree_non_null = set()  # Task which need more arcs

    # Make the set: task with non null degree
    for task in dataflow.get_task_list():
        if task_degree[task] > 0:
            task_degree_non_null.add(task)
    for task in task_degree_non_null.copy():  # Start iterate on task to add arc
        if task_degree[task] > 0:
            task_to_rm = []  # Temporary ignored task because of non reentrant or non multi-arc param
            if not c_param.is_reentrant():
                task_to_rm.append(task)
            if not c_param.is_multi_arc():
                for arc in dataflow.get_arc_list(source=task):
                    task_p = dataflow.get_target(arc)
                    if len(dataflow.get_arc_list(source=task_p, target=task)) > 0:
                        task_to_rm.append(task_p)
            # Compute potential task to add arc from task_degree_non_null and task_to_rm
            for rm_task in task_to_rm:
                task_degree_non_null.discard(rm_task)

        # Add arc on potential task
        for _ in xrange(task_degree[task]):
            if len(task_degree_non_null) > 0:
                random_task = sample(task_degree_non_null, 1)[0]
                arc_created = False
                if not c_param.is_multi_arc():
                    if dataflow.get_arc_list(source=random_task, target=task):
                        dataflow.add_arc(task, random_task)
                        arc_created = True
                    elif dataflow.get_arc_list(source=task, target=random_task):
                        dataflow.add_arc(random_task, task)
                        arc_created = True

                if not arc_created:
                    if randint(0, 1):
                        dataflow.add_arc(task, random_task)
                    else:
                        dataflow.add_arc(random_task, task)

                task_degree[random_task] -= 1
                if task_degree[random_task] <= 0:
                    task_degree_non_null.discard(random_task)
                if not c_param.is_multi_arc():
                    arc_list = dataflow.get_arc_list(source=random_task, target=task)
                    arc_list += dataflow.get_arc_list(source=task, target=random_task)
                    if not c_param.is_multi_arc() and len(arc_list) == 2 or task_degree[random_task] == 0:
                        if task_degree[random_task] > 1:
                            task_to_rm.append(random_task)
                        task_degree_non_null.discard(random_task)
                arc_count += 1
                if dataflow.get_task_count() >= 1000 and arc_count % 1000 == 0:
                    logging.info(str(arc_count) + "/" + str(nb_tot_arcs) + " arcs added.")

        task_degree[task] = 0
        task_degree_non_null.discard(task)


def __generate_connex_dag(dataflow, c_param):
    logging.info("Generate connex directed acyclic graph")
    # First generate a path graph with x nodes and x-1 arcs
    if c_param.get_nb_task() < 10:
        path_nodes_nb = randint(2, int(c_param.get_nb_task() / 2))
    else:
        path_nodes_nb = int(c_param.get_nb_task() / randint(2, int(c_param.get_nb_task() / 2)))

    # Generate random degree for each task and emergency task in case of low average degree
    task_degree = []
    potential_emergency_task = set()
    emergency_task = set()
    for task in xrange(c_param.get_nb_task()):  # Compute degree wanted for each task
        task_degree.append(randint(c_param.get_min_task_degree(), c_param.get_max_task_degree()))
        if task_degree[task] < c_param.get_max_task_degree():
            potential_emergency_task.add(task)

    task_degree_non_null = set([])
    task_rank = {}

    # Create a path
    task = dataflow.add_task()
    task_degree_non_null.add(task)
    __try_add_emergency_task(task, potential_emergency_task, emergency_task)
    task_rank[task] = 0
    for i in xrange(1, path_nodes_nb):
        next_task = dataflow.add_task()
        task_degree_non_null.add(next_task)

        __try_add_emergency_task(next_task, potential_emergency_task, emergency_task)
        dataflow.add_arc(task, next_task)

        for t in [task, next_task]:
            task_degree[t] -= 1
            if task_degree[t] <= 0:
                task_degree_non_null.discard(t)
            if task_degree[t] < 0:
                emergency_task.discard(t)

        task = next_task
        task_rank[task] = i

    if c_param.get_nb_task() - path_nodes_nb > 0:
        for i in xrange(c_param.get_nb_task() - path_nodes_nb):
            path_rank = randint(0, path_nodes_nb - 1)
            task = dataflow.add_task()
            task_rank[task] = path_rank
            arc_added, random_task = __add_random_dag_arc(dataflow, task_degree_non_null, task, task_rank)
            if not arc_added:
                arc_added, random_task = __add_random_dag_arc(dataflow, emergency_task, task, task_rank)
                if not arc_added:
                    raise Exception("No emergency task, report it to the dev !")
                emergency_task.remove(random_task)
            task_degree_non_null.add(task)
            __try_add_emergency_task(task, potential_emergency_task, emergency_task)
            for t in [task, random_task]:
                task_degree[t] -= 1
                if task_degree[t] <= 0:
                    task_degree_non_null.discard(t)
    return task_rank, task_degree


def __generate_arcs_dag(dataflow, c_param, task_rank, task_degree):
    logging.info("Generate more arcs")
    nb_tot_arcs = dataflow.get_task_count() - 1
    arc_count = dataflow.get_task_count() - 1

    task_degree_non_null = set()
    for task in dataflow.get_task_list():
        if task_degree[task] > 0:
            nb_tot_arcs += task_degree[task]
            task_degree_non_null.add(task)

    # Make the set: task with non null degree
    for task in task_degree_non_null.copy():  # Start iterate on task to add arc
        if task_degree[task] > 0:
            task_degree_non_null.remove(task)
            task_to_rm = []  # Temporary ignored task because of non reentrant or non multi-arc param
            if not c_param.is_multi_arc():
                for taskp in task_degree_non_null:
                    if task_rank[task] > task_rank[taskp]:
                        if dataflow.get_arc_list(source=taskp, target=task):
                            task_to_rm.append(taskp)
                    elif task_rank[task] < task_rank[taskp]:
                        if dataflow.get_arc_list(source=task, target=taskp):
                            task_to_rm.append(taskp)
                    else:
                        if task > taskp and dataflow.get_arc_list(source=task, target=taskp):
                            task_to_rm.append(taskp)
                        if task < taskp and dataflow.get_arc_list(source=taskp, target=task):
                            task_to_rm.append(taskp)

            for rm_task in task_to_rm:
                task_degree_non_null.remove(rm_task)

            # Add arc on potential task
            for i in xrange(task_degree[task]):
                if task_degree_non_null:
                    random_task = __add_random_dag_arc(dataflow, task_degree_non_null, task, task_rank)[1]
                    task_degree[random_task] -= 1
                    if task_degree[random_task] <= 0:
                        task_degree_non_null.remove(random_task)
                    elif not c_param.is_multi_arc():
                        task_degree_non_null.discard(random_task)
                        task_to_rm.append(random_task)

                    arc_count += 1
                    if dataflow.get_task_count() >= 1000 and arc_count % 1000 == 0:
                        logging.info(str(arc_count) + "/" + str(nb_tot_arcs) + " arcs added.")

            # Put back task temporally removed
            for task_rm in task_to_rm:
                task_degree_non_null.add(task_rm)
            # Remove the task handle this iteration
            task_degree[task] = 0


def __add_random_dag_arc(dataflow, task_degree_non_null, task, task_rank):
    try:
        random_task = sample(task_degree_non_null, 1)[0]
    except ValueError:
        return False, None
    if task_rank[task] > task_rank[random_task]:
        dataflow.add_arc(random_task, task)
    elif task_rank[task] < task_rank[random_task]:
        dataflow.add_arc(task, random_task)
    else:  # If on the same rank
        if task > random_task:  # Check which task was created last
            dataflow.add_arc(task, random_task)
        else:
            dataflow.add_arc(random_task, task)
    return True, random_task


def __try_add_emergency_task(task, potential_emergency_task, emergency_task):
    try:
        potential_emergency_task.remove(task)
        emergency_task.add(task)
    except KeyError:
        pass

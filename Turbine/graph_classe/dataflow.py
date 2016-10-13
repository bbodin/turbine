import logging

import networkx as nx

from Turbine.algorithms.normalized import normalized_dataflow, un_normalized_dataflow
from Turbine.algorithms.rv import compute_rep_vect
from Turbine.algorithms.symbolic_exe import SymbolicExe
from Turbine.generation.marking_computation import compute_initial_marking


class Dataflow(object):
    ########################################################################
    #                           CONSTANT                                   #
    ########################################################################
    # --------------------------Task----------------------------------------#
    _CONST_TASK_NAME = "tName"
    _CONST_TASK_REPETITION_FACTOR = "repFac"

    # --------------------------Arc-----------------------------------------#
    _CONST_ARC_NAME = "aName"

    _CONST_ARC_PRELOAD = "aPrel"
    _CONST_ARC_TOKEN_SIZE = "tokS"
    _CONST_ARC_GCD = "aGcd"

    _CONST_ARC_CONS_PORT_NAME = "cPN"
    _CONST_ARC_PROD_PORT_NAME = "pPN"

    def __init__(self, name=""):
        """

        :type name: basestring
        """
        self.name = name
        self.nxg = nx.MultiDiGraph(name=name)
        self.task_key = 0
        self.arc_key = 0

        self.taskByName = {}
        self.arcByName = {}

    def __str__(self):
        ret = "Name: " + str(self.name) + "\n"
        ret += "Graph Properties: "
        if self.is_cyclic:
            ret += "cyclic, "
        else:
            ret += "dag, "
        if self.is_reentrant:
            ret += "reentrant"
        else:
            ret += "not reentrant"
        if self.is_multi_graph:
            ret += ", multi-graph\n"
        else:
            ret += ", not multi-graph\n"
        ret += "Task count: " + str(self.get_task_count()) + ", Arc count: " + str(self.get_arc_count()) + "\n"
        tot = 0
        for arc in self.get_arc_list():
            tot += self.get_initial_marking(arc)
        ret += "Tot initial marking: " + str(tot)
        return ret

    def set_name(self, name):
        self.name = name

    def draw(self):
        nx.draw(self.nxg)
        import matplotlib.pyplot as plt
        plt.show()

    def draw_to_pdf(self, name="dataflow"):
        from Turbine.draw.draw_dot import Dot
        d = Dot(self)
        d.write_pdf(name)

    ########################################################################
    #                           add/modify tasks                           #
    ########################################################################
    def add_task(self, name=None):
        """

        :type name: basestring
        """
        new_task = self.task_key
        if name is None:
            name = "t" + str(new_task)

        try:  # Detect if a task with the same name exist
            self.get_task_by_name(name)
            logging.error("Name already used by another task")
            return None  # If it is the case the present task is not add.
        except KeyError:
            pass

        self.task_key += 1
        self.taskByName[name] = new_task

        self.nxg.add_node(new_task)
        self.set_task_name(new_task, name)

        return new_task

    def rm_task(self, task):
        """Remove a task in the graph and all adjacent arcs.

        Parameters
        ----------
        task : the id of the task.
        """
        self.nxg.remove_node(task)

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_task_by_name(self, name):
        """:return : a task according to its name.

        Parameters
        ----------
        name : the name of the task.
        """
        return self.taskByName[name]

    def get_task_list(self):
        """Return the list of task of the graph.
        """
        return self.nxg.nodes()

    def get_task_name(self, task):
        """:return : the name of a task.

        Parameters
        ----------
        :param task: the specific task
        """
        return self.nxg.node[task][self._CONST_TASK_NAME]

    @staticmethod
    def get_source(arc):
        """:return : the source as a task of the arc.

        Parameters
        ----------
        :param arc: a tuple (source, target) or (source, target, key).

        :return :s
        -------
        Task source.
        """
        return arc[0]

    @staticmethod
    def get_target(arc):
        """:return : the target as a task of the arc.

        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).

        :return :s
        -------
        Task target.
        """
        return arc[1]

    def get_successors(self, task):
        """Return successors of a task.

        :return :
        ----------
        A list a successors.
        """
        return self.nxg.successors(task)

    def get_predecessors(self, task):
        """:return : predecessors of a task.

        :return :
        ----------
        A list a predecessors.
        """
        return self.nxg.predecessors(task)

    def get_input_degree(self, task):
        """:return : the input degree of a task.

        :return :
        ----------
        An integer.
        """
        return self.nxg.in_degree(task)

    def get_output_degree(self, task):
        """:return : the output degree of a task.

        :return int
        ----------
        An integer.
        """
        return self.nxg.out_degree(task)

    def get_repetition_factor(self, task):
        """:return : the repetition factor of a task.

        :return :
        ----------
        An integer.
        """
        return self.nxg.node[task][self._CONST_TASK_REPETITION_FACTOR]

    def _get_task_attribute(self, task, attrib_name):
        """Get the arc attribute with the attribute name attribName.

        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).

        :return :s
        -------
        the attribute asked.
        """
        try:
            return self.nxg.node[task][attrib_name]
        except:
            raise KeyError("Attribute " + attrib_name + " of task ref " + str(task) + " not found")

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~SETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def set_task_name(self, task, name):
        """Modify the name of the task in parameters.

        Parameters
        ----------
        task : the task targeted.
        name : the name of the task.
        """
        self.nxg.node[task][self._CONST_TASK_NAME] = name
        return name

    def set_repetition_factor(self, task, repetition_factor):
        """Modify the repetition factor of a task.

        Parameters
        ----------
        task : the task targeted.
        repetitionFactor : the new repetition factor (integer).
        """
        self.nxg.node[task][self._CONST_TASK_REPETITION_FACTOR] = repetition_factor

    def _set_task_attribute(self, task, attrib, attrib_name):
        """Get the arc attribute with the attribute name attribName.

        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).

        :return :s
        -------
        the attribute asked.
        """
        self.nxg.node[task][attrib_name] = attrib

    ########################################################################
    #                           add/modify arcs                            #
    ########################################################################
    def add_arc(self, source, target):
        """Add an arc in the graph and initialize all his list according
        to the number of phase of both tasks.

        Parameters
        ----------
        source : the name of a task you already add on the graph.
        target : the name of a task you already add on the graph.

        :return :
        ------
        the tuple (source,target, key).
        """

        self.nxg.add_edge(source, target)
        key = self.nxg.edge[source][target].items()[-1][0]
        arc = (source, target, key)

        self.set_initial_marking(arc, 0)
        self.set_token_size(arc, 1)

        self.set_cons_port_name(arc, "cons" + str(source) + "" + str(target) + "" + str(key))
        self.set_prod_port_name(arc, "prod" + str(source) + "" + str(target) + "" + str(key))

        arc_name = "a" + str(self.arc_key)
        self.arc_key += 1

        self.set_arc_name(arc, arc_name)

        return arc  # return the tuple (source, target, key)

    def rm_arc(self, arc):
        """Remove an edge (arc of the graph.

        Parameters
        ----------
        arc : the arc to remove.
        """
        self.nxg.remove_edge(arc[0], arc[1], arc[2])

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of arcs~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def get_arc_by_name(self, name):
        """:return : an arc according to his name.

        Parameters
        ----------
        Name of an arc.

        :return :s
        -------
        arc: a tuple (source, target) or (source, target, key).
        """
        return self.arcByName[name]

    def get_arc_name(self, arc):
        """Return the name of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self._get_arc_attribute(arc, self._CONST_ARC_NAME)

    def get_arc_list(self, source=None, target=None):
        """:return : an arc according to parameters filled.
        if none of parameters are filled, the method return all arcs of the graph
        if only the source is filled, the method return all outputs arcs of the source
        if only the target is filled, the method return all inputs arcs of the target

        Parameters
        ----------
        :param source: source task.
        :param target: target task.

        :return :s
        -------
        A vector of arcs.

        """
        if source is None and target is not None:  # target is filled, the method returns all input arcs of the target
            return self.nxg.in_edges(target, keys=True)
        if source is not None and target is None:  # source is filled, the method returns all output arcs of the source
            return self.nxg.out_edges(source, keys=True)
        if source is None and target is None:  # Nothing is filled, the method return all arcs of the graph
            return self.nxg.edges(keys=True)
        # Both source and target are filled, the method return all arcs
        # with the source has a source and the target has a target.
        return [x for x in self.nxg.in_edges(target, keys=True) if self.get_source(x) == source]

    def get_initial_marking(self, arc):
        """:return : the initial marking of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self._get_arc_attribute(arc, self._CONST_ARC_PRELOAD)

    def get_token_size(self, arc):
        """:return : the token size of an arc (default 1).

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self._get_arc_attribute(arc, self._CONST_ARC_TOKEN_SIZE)

    def get_initial_marking_size(self, arc):
        """:return : the size of the arc in memory.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.get_initial_marking(arc) * self.get_token_size(arc)

    def get_cons_port_name(self, arc):
        """:return : the consumption port name of an arc. This is used only for sdf3 files .

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self._get_arc_attribute(arc, self._CONST_ARC_CONS_PORT_NAME)

    def get_prod_port_name(self, arc):
        """:return : the production port name of an arc. This is used only for sdf3 files.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self._get_arc_attribute(arc, self._CONST_ARC_PROD_PORT_NAME)

    def get_gcd(self, arc):
        return self._get_arc_attribute(arc, self._CONST_ARC_GCD)

    def _get_arc_attribute(self, arc, attrib_name):
        """Get the arc attribute with the attribute name attribName.

        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).

        :return :s
        -------
        the attribute asked.
        """
        try:
            return self.nxg[arc[0]][arc[1]][arc[2]][attrib_name]
        except:
            raise KeyError("Attribute " + attrib_name + " of arc ref " + str(arc) + " not found")

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~SETTER of arcs~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_arc_name(self, arc, name):
        """Set the name of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        name : (string) the arc name.
        """
        try:
            if self.get_arc_by_name(name) != arc:
                logging.error("Name already used by another arc !")
                return
        except KeyError:
            pass

        self._set_arc_attribute(arc, str(name), self._CONST_ARC_NAME)

    def set_initial_marking(self, arc, initial_marking):
        """Set the initial marking of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        preload : (integer) the value of the initial marking.
        """
        self._set_arc_attribute(arc, initial_marking, self._CONST_ARC_PRELOAD)

    def set_token_size(self, arc, token_size):
        """Set the token size of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        tokenSize : the token size of this bds/arc (integer).
        """
        self._set_arc_attribute(arc, token_size, self._CONST_ARC_TOKEN_SIZE)

    def set_cons_port_name(self, arc, cons_port_name):
        """Set the consumption port name of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consPortName : the name of the consumption port name.

        This is only used with the SDF3 sol_file_parser.
        """
        self._set_arc_attribute(arc, cons_port_name, self._CONST_ARC_CONS_PORT_NAME)

    def set_prod_port_name(self, arc, prod_port_name):
        """Set the production port name in an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        prodPortName : the name of the production port name.

        This is only used with the SDF3 sol_file_parser.
        """
        self._set_arc_attribute(arc, prod_port_name, self._CONST_ARC_PROD_PORT_NAME)

    def _set_arc_attribute(self, arc, attrib, attrib_name):
        """Set a specific attribute to the arc (prelo/cPoNa/pPoNa/...).

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        attrib : (integer) the value of the attribute.
        attribName : (string) the attribute name.
        """
        self.nxg[arc[0]][arc[1]][arc[2]][attrib_name] = attrib

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~PROPERTIES of arcs~~~~~~~~~~~~~~~~~~~~~~~ #
    def is_arc_reentrant(self, arc):
        """:return : True if the arc is reentrant.

        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).
        """
        source = self.get_source(arc)
        target = self.get_target(arc)
        return source == target

    ########################################################################
    #                            GETTER graph                              #
    ########################################################################
    def get_task_count(self):
        """:return : the number of task of the graph.
        """
        return self.nxg.number_of_nodes()

    def get_arc_count(self):
        """:return : the number of arc of the graph.
        """
        return self.nxg.number_of_edges()

    def get_name(self):
        """:return : the name of the graph.
        """
        return self.name

    def get_tot_initial_marking(self):
        im_sum = 0
        for arc in self.get_arc_list():
            im_sum += self.get_initial_marking(arc)
        return im_sum

    def get_tot_size(self):
        sum_size = 0
        for arc in self.get_arc_list():
            sum_size += self.get_initial_marking_size(arc)
        return sum_size


    ########################################################################
    #                        Graph Transformations                         #
    ########################################################################
    def compute_initial_marking(self, solver_str="Auto", solver_verbose=False, lp_filename=None, period=None):
        """Generate the initial marking of the graph such that it's became alive.
        Initial marking computation is handle by GLPK (freeware) a linear solver or GUROBI (free for university).

        Parameters
        ----------
        :type solver_str: str, the solver which compute the initial marking (SC1 or SC2).
        If default (None) the solver choose by comparing the number of constraints related to sufficient condition
        (SC1 or SC2).
        :type solver_verbose: bool, if True the terminal will show GLPK informations.
        :type lp_filename: str, if not None, the solver will write the linear program used to compute initial marking.
        :type period: int,
        """
        compute_initial_marking(self, solver_str=solver_str, solver_verbose=solver_verbose,
                                lp_filename=lp_filename, period=period)

    def compute_repetition_vector(self):
        return compute_rep_vect(self)

    def normalized(self, vect=None):
        return normalized_dataflow(self, coef_vector=vect)

    def un_normalized(self, coef_vector=None):
        return un_normalized_dataflow(self, coef_vector=coef_vector)

    def del_initial_marking(self):
        """Set all initial marking to zero.
        """
        for arc in self.get_arc_list():
            self.set_initial_marking(arc, 0)

    ########################################################################
    #                        PROPERTIES graph                              #
    ########################################################################
    @property
    def is_multi_graph(self):
        """:return : True if the graph is a multi-graph
        (i.e. if there exist two arc from a task to another).
        """
        for arc in self.get_arc_list():
            source, target = self.get_source(arc), self.get_target(arc)
            if len(self.get_arc_list(source=source, target=target)) > 1:
                return True
        return False

    @property
    def is_reentrant(self):
        """:return : True if the graph is re-entrant
        (i.e. if there is at least one arc such as the source and the target are the same task)
        """
        for arc in self.get_arc_list():
            if self.is_arc_reentrant(arc):
                return True
        return False

    @property
    def is_cyclic(self):
        """:return : True if the graph has cycle (reentrant arcs are not considerate as cycle).
        """
        if self.is_reentrant:
            return True
        return not nx.is_directed_acyclic_graph(self.nxg)
        # return max(len(cc) for cc in nx.strongly_connected_components(self.nxg)) > 1

    @property
    def is_bounded(self):
        """

        :return: True if for every arc its backward (back pressure) arc exist
        """
        for arc in self.get_arc_list():
            task1 = self.get_source(arc)
            task2 = self.get_target(arc)
            l1 = len(self.get_arc_list(source=task1, target=task2))
            l2 = len(self.get_arc_list(source=task2, target=task1))
            if l1 == 1 and l2 == 0:
                return False
            if l2 == 1 and l1 == 0:
                return False
        return True

    @property
    def is_dead_lock(self):
        """
        :return: True if the dataflow is dead lock
        """
        se = SymbolicExe(self)
        if se.execute() == 0:
            return False
        return True

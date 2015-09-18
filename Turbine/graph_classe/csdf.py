from fractions import gcd

from Turbine.graph_classe.dataflow import Dataflow


class CSDF(Dataflow):
    ########################################################################
    #                           CONSTANT                                   #
    ########################################################################
    # -------------------------Task----------------------------------------#
    CONST_PHASE_DURATION_LIST = "pDurL"

    # -------------------------Arc-----------------------------------------#
    CONST_ARC_CONS_RATE_LIST = "cL"
    CONST_ARC_PROD_RATE_LIST = "pL"

    def __init__(self, name=""):
        """

            :type name: basestring
            """
        super(CSDF, self).__init__(name)

    def __str__(self):
        ret = super(CSDF, self).__str__()
        ret += "\nNormalized: "+str(self.is_normalized)+"\n"
        return ret

    def __eq__(self, other):
        for arc in self.get_arc_list():
            if self.get_cons_str(arc) != other.get_cons_str(arc):
                return False
            if self.get_prod_str(arc) != other.get_prod_str(arc):
                return False
        for task in self.get_task_list():
            if self.get_duration_str(task) != other.get_duration_str(task):
                return False
        return True

    @staticmethod
    def get_dataflow_type():
        return "CSDF"

    @property
    def is_sdf(self):
        return False

    @property
    def is_csdf(self):
        return True

    @property
    def is_pcg(self):
        return False

    ########################################################################
    #                           add/modify tasks                           #
    ########################################################################
    def add_task(self, name=None):
        """
        :param name: str
        """
        new_task = super(CSDF, self).add_task(name)
        self.set_phase_count(new_task, 1)
        return new_task

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_phase_count(self, task):
        return len(self._get_task_attribute(task, self.CONST_PHASE_DURATION_LIST))

    def get_phase_duration_list(self, task):
        return self._get_task_attribute(task, self.CONST_PHASE_DURATION_LIST)

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~SETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_phase_count(self, task, phase_count):
        """Modify the phase count of a task and initialize the list of all connected arc's
        cyclic phase.

        Parameters
        ----------
        task : the name of the task you want modify.
        :type phase_count: int

        Note that if (and only if) the phase count is different than the previous one,
        all incidents arcs will have their cyclic weights reinitialized.
        """
        # If the number of phase is the same as before, do nothing
        try:
            if phase_count == self.get_phase_count(task):
                return
        except KeyError:
            pass

        self.nxg.node[task][self.CONST_PHASE_DURATION_LIST] = [1] * phase_count

        for arc in self.get_arc_list(target=task):
            self.set_cons_rate_list(arc, [1] * phase_count)

        for arc in self.get_arc_list(source=task):
            self.set_prod_rate_list(arc, [1] * phase_count)

    def set_phase_duration_list(self, task, phase_duration_list):
        """Modify the phase duration list of a task.

        Parameters
        ----------
        task : the task targeted.
        :type phase_duration_list : list the list of phase duration of the task (integer).
        """
        self.__verify_length(task, len(phase_duration_list))
        self.nxg.node[task][self.CONST_PHASE_DURATION_LIST] = phase_duration_list

    def __verify_length(self, task, length_list):
        """Compare the length of a list and the phase number of a task.

        Parameters
        ----------
        task : the task targeted.
        :type length_list : int the size of the list.

        Returns:
        -------
        True if both length corresponds.
        """
        if length_list != self.get_phase_count(task):
            raise BaseException("On task " + str(task) + " : the length of the phase list (" + str(length_list) +
                                ") does not match with the phase count of the task ("
                                + str(self.get_phase_count(task)) + ")")

    ########################################################################
    #                           add/modify arc                             #
    ########################################################################
    def add_arc(self, source, target):
        """

        :param source: task
        :param target: task
        """
        arc = super(CSDF, self).add_arc(source, target)
        source_pc = self.get_phase_count(source)
        target_pc = self.get_phase_count(target)
        self.set_cons_rate_list(arc, [1]*target_pc)
        self.set_prod_rate_list(arc, [1]*source_pc)
        return arc

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of arcs~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_cons_rate_list(self, arc):
        return self._get_arc_attribute(arc, self.CONST_ARC_CONS_RATE_LIST)

    def get_prod_rate_list(self, arc):
        return self._get_arc_attribute(arc, self.CONST_ARC_PROD_RATE_LIST)

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~SETTER of arcs~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_cons_rate_list(self, arc, cons_rate_list):
        """Set the consumption list of an arc.

        Parameters
        ----------
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).

        :type cons_rate_list: list of integer
        """
        self._set_arc_attribute(arc, cons_rate_list, self.CONST_ARC_CONS_RATE_LIST)
        self._calc_gcd(arc)

    def set_prod_rate_list(self, arc, prod_rate_list):
        """Set the consumption list of an arc.

        Parameters
        ----------
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).

        :type prod_rate_list: list of integer
        """
        self._set_arc_attribute(arc, prod_rate_list, self.CONST_ARC_PROD_RATE_LIST)
        self._calc_gcd(arc)

    def _calc_gcd(self, arc):
        """Calculate the GCD between the consumption weight list and the
        production weight list of an arc.

        Parameters
        ----------
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try:
            a = reduce(gcd, self.get_cons_rate_list(arc))
            b = reduce(gcd, self.get_prod_rate_list(arc))
            gcd_v = gcd(a, b)
            self._set_arc_attribute(arc, gcd_v, self.CONST_ARC_GCD)
        except KeyError:
            pass

    ########################################################################
    #                           GETTER for the parser                      #
    ########################################################################
    def get_prod_str(self, arc):
        """Return a string which recapitulate of consumption vectors of an arc.

        Parameters
        ----------
        :rtype : str
        :param : arc tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        result = ""
        for i in range(0, self.get_phase_count(arc[0])):
            result += str(int(self.get_prod_rate_list(arc)[i])) + ","
        return result[0:-1]  # del the last comma

    def get_cons_str(self, arc):
        """Return a string which recapitulate of consumption vectors of an arc.

        Parameters
        ----------
        :rtype : str
        :param : arc tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        result = ""
        for i in range(0, self.get_phase_count(arc[1])):
            result += str(int(self.get_cons_rate_list(arc)[i])) + ","
        return result[0:-1]  # del the last comma

    def get_duration_str(self, task):
        """Return task (initial and normal) phase duration list as a string.

        Parameters
        ----------
        :rtype : str
        """
        result = str([int(i) for i in self.get_phase_duration_list(task)])[1:-1]
        return result.replace(" ", "")

    ########################################################################
    #                        PROPERTIES graph                              #
    ########################################################################
    @property
    def is_normalized(self):
        """:return : True if the graph is a normalized
        (i.e. if every adjacent weights of a task (prod or cons) are equal).
        """
        for task in self.get_task_list():
            try:
                weight = sum(self.get_prod_rate_list(self.get_arc_list(source=task)[0]))
            except IndexError:
                weight = sum(self.get_cons_rate_list(self.get_arc_list(target=task)[0]))
            for arc in self.get_arc_list(source=task):
                if sum(self.get_prod_rate_list(arc)) != weight:
                    return False
            for arc in self.get_arc_list(target=task):
                if sum(self.get_cons_rate_list(arc)) != weight:
                    return False
        return True

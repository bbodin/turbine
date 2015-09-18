from fractions import gcd

from Turbine.graph_classe.dataflow import Dataflow
from Turbine.period.period_computation import ComputePeriod


class SDF(Dataflow):
    ########################################################################
    #                           CONSTANT                                   #
    ########################################################################
    # -------------------------Task----------------------------------------#
    CONST_TASK_DURATION = "tDur"

    # -------------------------Arc-----------------------------------------#
    CONST_ARC_CONS_RATE = "cL"
    CONST_ARC_PROD_RATE = "pL"

    def __init__(self, name=""):
        """

        :type name: str
        """
        super(SDF, self).__init__(name=name)

    def __str__(self):
        ret = super(SDF, self).__str__()
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
        return "SDF"

    @property
    def is_sdf(self):
        return True

    @property
    def is_csdf(self):
        return False

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
        task = super(SDF, self).add_task(name)
        self.set_task_duration(task, 1)
        return task

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_task_duration(self, task):
        return self._get_task_attribute(task, self.CONST_TASK_DURATION)

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~SETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_task_duration(self, task, duration):
        """

        :type duration: int
        """
        return self._set_task_attribute(task, duration, self.CONST_TASK_DURATION)

    ########################################################################
    #                           add/modify arcs                            #
    ########################################################################
    def add_arc(self, source, target):
        """

        :param source: task
        :param target: task
        """
        arc = super(SDF, self).add_arc(source, target)
        self.set_cons_rate(arc, 1)
        self.set_prod_rate(arc, 1)
        return arc

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of arcs~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_cons_rate(self, arc):
        return self._get_arc_attribute(arc, self.CONST_ARC_CONS_RATE)

    def get_prod_rate(self, arc):
        return self._get_arc_attribute(arc, self.CONST_ARC_PROD_RATE)

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~SETTER of arcs~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_cons_rate(self, arc, cons_rate):
        """Set the consumption list of an arc.

        Parameters
        ----------
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).

        :type cons_rate: int
        """
        self._set_arc_attribute(arc, cons_rate, self.CONST_ARC_CONS_RATE)
        self.__calc_gcd(arc)

    def set_prod_rate(self, arc, prod_rate):
        """Set the consumption list of an arc.

        Parameters
        ----------
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).

        :type prod_rate: int
        """
        self._set_arc_attribute(arc, prod_rate, self.CONST_ARC_PROD_RATE)
        self.__calc_gcd(arc)

    def __calc_gcd(self, arc):
        """Calculate the GCD between the consumption weight list and the
        production weight list of an arc.

        Parameters
        ----------
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try:
            gcd_v = gcd(self.get_cons_rate(arc), self.get_prod_rate(arc))
            self._set_arc_attribute(arc, gcd_v, self.CONST_ARC_GCD)
        except KeyError:
            pass

    ########################################################################
    #                           GETTER for the parser                      #
    ########################################################################
    def get_cons_str(self, arc):
        """Return a string which recapitulate of consumption vectors of an arc.

        Parameters
        ----------
        :rtype : str
        :param arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return str(self.get_cons_rate(arc))

    def get_prod_str(self, arc):
        """Return a string which recapitulate of consumption vectors of an arc.

        Parameters
        ----------
        :rtype : str
        :param arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return str(self.get_prod_rate(arc))

    def get_duration_str(self, task):
        """Return task (initial and normal) phase duration list as a string.

        Parameters
        ----------
        :rtype : str
        """
        return str(self.get_task_duration(task))

    def get_period(self):
        pc = ComputePeriod(self)
        return pc.compute_period()

    ########################################################################
    #                        PROPERTIES graph                              #
    ########################################################################
    @property
    def is_consistent(self):
        """Return True if the graph is consistent.
        """
        for arc in self.get_arc_list():
            source_w = sum(self.get_prod_rate(arc)) * self.get_repetition_factor(self.get_source(arc))
            target_w = sum(self.get_cons_rate(arc)) * self.get_repetition_factor(self.get_target(arc))
            if source_w != target_w:
                return False
        return True

    @property
    def is_normalized(self):
        """:return : True if the graph is a normalized
        (i.e. if every adjacent weights of a task (prod or cons) are equal).
        """
        for task in self.get_task_list():
            try:
                weight = self.get_prod_rate(self.get_arc_list(source=task)[0])
            except IndexError:
                weight = self.get_cons_rate(self.get_arc_list(target=task)[0])

            for arc in self.get_arc_list(source=task):
                if not self.get_prod_rate(arc) == weight:
                    return False
            for arc in self.get_arc_list(target=task):
                if not self.get_cons_rate(arc) == weight:
                    return False
        return True

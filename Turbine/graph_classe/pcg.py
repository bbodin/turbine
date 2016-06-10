from fractions import gcd

from Turbine.graph_classe.csdf import CSDF


class PCG(CSDF):
    ########################################################################
    #                           CONSTANT                                   #
    ########################################################################
    # -------------------------Task----------------------------------------#
    __CONST_INI_PHASE_DURATION_LIST = "iniPhaDurL"

    # -------------------------Arc-----------------------------------------#
    __CONST_ARC_INI_CONS_RATE_LIST = "iniCL"
    __CONST_ARC_INI_PROD_RATE_LIST = "iniPL"

    __CONST_ARC_THRESHOLD_LIST = "thrL"
    __CONST_ARC_INI_THRESHOLD_LIST = "iniThrL"

    def __init__(self, name=""):
        """

        :type name: basestring
        """
        super(PCG, self).__init__(name=name)

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
        return "PCG"

    @property
    def is_sdf(self):
        return False

    @property
    def is_csdf(self):
        return True

    @property
    def is_pcg(self):
        return True


    ########################################################################
    #                           add/modify tasks                           #
    ########################################################################
    def add_task(self, name=None):
        """
        :param name: str
        """
        new_task = super(PCG, self).add_task(name)
        self.set_ini_phase_count(new_task, 0)
        return new_task

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_ini_phase_count(self, task):
        return len(self._get_task_attribute(task, self.__CONST_INI_PHASE_DURATION_LIST))

    def get_ini_phase_duration_list(self, task):
        return self._get_task_attribute(task, self.__CONST_INI_PHASE_DURATION_LIST)

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~SETTER of tasks~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_ini_phase_count(self, task, ini_phase_count):
        """Modify the phase count of a task and initialize the list of all connected arc's
        cyclic phase.

        Parameters
        ----------
        task : the name of the task you want modify.
        phaseCount : the number of phase of the task (integer).

        Note that if (and only if) the phase count is different than the previous one,
        all incidents arcs will have their cyclic weights reinitialized.
        """
        # If the number of phase is the same as before, do nothing
        try:
            if ini_phase_count == self.get_ini_phase_count(task):
                return
        except KeyError:
            pass

        self.nxg.node[task][self.__CONST_INI_PHASE_DURATION_LIST] = [1] * ini_phase_count

        for arc in self.get_arc_list(target=task):
            self.set_ini_cons_rate_list(arc, [1] * ini_phase_count)

        for arc in self.get_arc_list(source=task):
            self.set_ini_prod_rate_list(arc, [1] * ini_phase_count)

    def set_ini_phase_duration_list(self, task, ini_phase_duration_list):
        """Modify the initial phase duration list of a task.

        Parameters
        ----------
        task : the task targeted.
        iniPhaseDurationList : the list of initial phase duration of the task (integer).
        """
        self.__verify_length_ini(task, len(ini_phase_duration_list))
        self._set_task_attribute(task, ini_phase_duration_list, self.__CONST_INI_PHASE_DURATION_LIST)

    def __verify_length_ini(self, task, length_list):
        """Compare the length of a list and the initial phase number of a task.

        Parameters
        ----------
        task : the task targeted.
        lengthList : the size of the list.

        Returns:
        -------
        True if both length corresponds.
        """
        if length_list != self.get_ini_phase_count(task):
            raise BaseException("On task " + str(task) +
                                " : the length of the initial phase list  (len=" + str(length_list) +
                                ")  does not match with the phase count of the task(count=" +
                                str(self.get_ini_phase_count(task)) + ")")

    ########################################################################
    #                           add/modify arc                             #
    ########################################################################
    def add_arc(self, source, target):
        """

        :param source: task
        :param target: task
        """
        arc = super(PCG, self).add_arc(source, target)
        target_ipc = self.get_ini_phase_count(self.get_target(arc))
        source_ipc = self.get_ini_phase_count(self.get_source(arc))
        self.set_ini_cons_rate_list(arc, [1]*target_ipc)
        self.set_ini_prod_rate_list(arc, [1]*source_ipc)
        return arc

    ########################################################################
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~GETTER of arcs~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_ini_cons_rate_list(self, arc):
        return self._get_arc_attribute(arc, self.__CONST_ARC_INI_CONS_RATE_LIST)

    def get_ini_prod_rate_list(self, arc):
        return self._get_arc_attribute(arc, self.__CONST_ARC_INI_PROD_RATE_LIST)

    def get_threshold_list(self, arc):
        return self._get_arc_attribute(arc, self.__CONST_ARC_THRESHOLD_LIST)

    def get_ini_threshold_list(self, arc):
        return self._get_arc_attribute(arc, self.__CONST_ARC_INI_THRESHOLD_LIST)

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
        super(PCG, self).set_cons_rate_list(arc, cons_rate_list)
        self.set_threshold_list(arc, cons_rate_list)
        self.__calc_gcd(arc)

    def set_ini_cons_rate_list(self, arc, ini_cons_rate):
        self._set_arc_attribute(arc, ini_cons_rate, self.__CONST_ARC_INI_CONS_RATE_LIST)
        self.set_ini_threshold_list(arc, ini_cons_rate)
        self.__calc_gcd(arc)

    def set_ini_prod_rate_list(self, arc, ini_prod_rate):
        self._set_arc_attribute(arc, ini_prod_rate, self.__CONST_ARC_INI_PROD_RATE_LIST)
        self.__calc_gcd(arc)

    def set_threshold_list(self, arc, threshold_list):
        self._set_arc_attribute(arc, threshold_list, self.__CONST_ARC_THRESHOLD_LIST)
        self.__calc_gcd(arc)

    def set_ini_threshold_list(self, arc, ini_threshold_list):
        self._set_arc_attribute(arc, ini_threshold_list, self.__CONST_ARC_INI_THRESHOLD_LIST)
        self.__calc_gcd(arc)

    def __calc_gcd(self, arc):
        """Calculate the GCD between the consumption weight lists (initial as well) the
        production weight lists (initial as well), and the threshold lists (initial as well) of an arc.

        Parameters
        ----------
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try:
            gcd_v = self.get_gcd(arc)
            if not self.get_ini_cons_rate_list == []:
                gcd_v = reduce(gcd, self.get_ini_cons_rate_list(arc)+[gcd_v])
            if not self.get_ini_prod_rate_list == []:
                gcd_v = reduce(gcd, self.get_ini_prod_rate_list(arc)+[gcd_v])
            if not self.get_threshold_list == []:
                gcd_v = reduce(gcd, self.get_threshold_list(arc)+[gcd_v])
            if not self.get_ini_threshold_list == []:
                gcd_v = reduce(gcd, self.get_ini_threshold_list(arc)+[gcd_v])
            self._set_arc_attribute(arc, gcd_v, self._CONST_ARC_GCD)
        except KeyError:
            pass

    ########################################################################
    #                           GETTER for the parser                      #
    ########################################################################
    def get_prod_str(self, arc):
        """Return a string which recapitulate of production vectors of an arc.

        Parameters
        ----------
        :rtype : str
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).

        Return
        ------
        The string look like : 1,2;3,6 which correspond to
            before the semicolon :
                initial production : 1,2
            after the semicolon :
                production : 3,6
        """
        result = ""
        for i in range(0, self.get_ini_phase_count(arc[0])):
            result += str(int(self.get_ini_prod_rate_list(arc)[i])) + ","
        if len(result) > 0:
            result = result[0:-1] + ";"  # del the last comma
        for i in range(0, self.get_phase_count(arc[0])):
            result += str(int(self.get_prod_rate_list(arc)[i])) + ","
        return result[0:-1]  # del the last comma

    def get_cons_str(self, arc):
        """Return a string which recapitulate of consumption vectors of an arc.

        Parameters
        ----------
        :rtype : str
        :type arc: tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).

        Return
        ------
        The string look like : 1:2,2;3:4,6 which correspond to :
            before the semicolon :
                initial consumption : 1,2
                initial threshold : 2,2
            after the semicolon :
                consumption : 3,6
                threshold : 4,6
        (when the threshold is equal to its consumption, it is not display).
        """
        result = ""
        if self.get_ini_phase_count(self.get_target(arc)) > 0:
            for i in range(0, self.get_ini_phase_count(self.get_target(arc))):
                if self.get_ini_cons_rate_list(arc)[i] != self.get_ini_threshold_list(arc)[i]:
                    result += str(int(self.get_ini_cons_rate_list(arc)[i]))\
                        + ":" + str(int(self.get_ini_threshold_list(arc)[i])) + ","
                else:
                    result += str(int(self.get_ini_cons_rate_list(arc)[i])) + ","
        if len(result) > 0:
            result = result[0:-1] + ";"  # del the last comma
        for i in range(0, self.get_phase_count(arc[1])):
            if self.get_cons_rate_list(arc)[i] != self.get_threshold_list(arc)[i]:
                result += str(int(self.get_cons_rate_list(arc)[i])) \
                    + ":" + str(int(self.get_threshold_list(arc)[i])) + ","
            else:
                result += str(int(self.get_cons_rate_list(arc)[i])) + ","
        return result[0:-1]  # del the last comma

    def get_duration_str(self, task):
        """Return task (initial and normal) phase duration list as a string.

        :rtype : str
        :type task: task
        """
        result = ""
        if self.get_phase_count(task) > 0:
            result = str([float(i) for i in self.get_phase_duration_list(task)])[1:-1]
        if self.get_ini_phase_count(task) > 0:
            ini = str([float(i) for i in self.get_ini_phase_duration_list(task)])[1:-1]
            if len(ini) > 0:
                return (str(ini) + ";" + str(result)).replace(" ", "")
            else:
                return str(result).replace(" ", "")
        return str(result).replace(" ", "")

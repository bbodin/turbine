import logging


class Parameters:
    """This class contains all options for generate dataflow dataflow
    """

    def __init__(self):

        # ~~~~~~~~~~~~~~~~~~~~~~GENERATOR~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # dataflow
        # Number of task in the dataflow
        self.__NB_TASK = 10
        # Minimum output/input arc count for the dataflow
        self.__MIN_TASK_DEGREE = 1
        # Maximum output/input arc count for the dataflow 
        self.__MAX_TASK_DEGREE = 3

        # PHASES
        # Minimum phase count for a task
        self.__MIN_PHASE_COUNT = 1
        # Maximum phase count for a task
        self.__MAX_PHASE_COUNT = 5
        # Average Time for a phase
        self.__AVERAGE_TIME = 10

        # INITIAL PHASES
        # Minimum initial phase count 
        self.__MIN_INI_PHASE_COUNT = 0
        # Maximum initial phase count 
        self.__MAX_INI_PHASE_COUNT = 2
        # Average Initial time for a phase
        self.__AVERAGE__INI_TIME = 10
        
        # ARC
        self.__AVERAGE_INI_WEIGHT = 10

        # TASK
        # Average repetition factor of a task
        self.__AVERAGE_RF = 5

        # ~~~~~~~~~~~~~~~~~~~~~~dataflow~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        self.__dataflow_TYPE = "SDF"

        # True: generate a normalized dataflow
        self.__NORMALIZED = False

        # True generate dataflow with re-entrant arc
        self.__REENTRANT = False

        # True generate dataflow with multi arc
        self.__MULTI_ARC = False

        # True generate an acyclic dataflow
        self.__ACYCLIC = False

        # ~~~~~~~~~~~~~~~~~~~~PRELOAD~SOLVER~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # Select the initial marking's solver
        self.__SOLVER = "Auto"
        
        # ~~~~~~~~~~~~~~~~~~~~PRINT~OPTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        self.__VERBOSE_SOLVER = False
        self.__LOGGING_LEVEL = logging.ERROR
        # The file name where the ILP of the initial marking's solver will be write
        self.__LP_FILENAME = None
        
    ########################################################################
    #                           SETTERS                                    #
    ########################################################################
    # dataflow
    def set_nb_task(self, value):
        """Set the number of task/actors of the dataflow dataflow.
        default: 10
        """
        self.__verify_integer_non_null(value)
        if value < 2:
            raise Exception("Wrong value: it must be greater than 1")
        self.__NB_TASK = int(value)

    def set_min_task_degree(self, value):
        """Set the minimum arcs count during the random selection of the dataflow dataflow.
        default: 1
        """        
        self.__verify_integer_non_null(value)
        self.__MIN_TASK_DEGREE = int(value)

    def set_max_task_degree(self, value):
        """Set the maximum arcs count during the random selection of the dataflow dataflow.
        default: 5
        """        
        self.__verify_integer_non_negativ(value)
        if value < 2:
            raise Exception("Max must be higher than 1")
        self.__MAX_TASK_DEGREE = int(value)

    # PHASES
    def set_min_phase_count(self, value):
        """Set task's minimum phase count during the random selection of the dataflow dataflow.
        default: 1
        """
        self.__verify_integer_non_null(value)
        self.__MIN_PHASE_COUNT = int(value)

    def set_max_phase_count(self, value):
        """Set task's maximum phase count during the random selection of the dataflow dataflow.
        default: 5
        """        
        self.__verify_integer_non_negativ(value)
        if value < self.get_min_phase_count():
            raise Exception("Max must be higher than min value")
        self.__MAX_PHASE_COUNT = int(value)

    def set_average_time(self, value):
        """Set phase's average time during the random selection of the dataflow dataflow.
        default: 10
        """        
        self.__verify_integer_non_null(value)
        self.__AVERAGE_TIME = int(value)

    # INITIAL PHASES
    def set_min_ini_phase_count(self, value):
        """Set task's minimum initial phase count during the random selection of the dataflow dataflow.
        default: 0
        """        
        self.__verify_integer_non_negativ(value)
        self.__MIN_INI_PHASE_COUNT = int(value)

    def set_max_ini_phase_count(self, value):
        """Set task's maximum phase count during the random selection of the dataflow dataflow.
        default: 2
        """        
        self.__verify_integer_non_negativ(value)
        if value < self.get_min_phase_count_ini():
            raise Exception("Max must be higher than min value")
        self.__MAX_INI_PHASE_COUNT = int(value)

    def set_average_ini_time(self, value):
        """Set initial phase's average time during the random selection of the dataflow dataflow.
        default: 10
        """        
        self.__verify_integer_non_negativ(value)
        self.__AVERAGE__INI_TIME = int(value)

    def set_average_ini_weight(self, value):
        """Set initial phase's average time during the random selection of the dataflow dataflow.
        default: 10
        """        
        self.__verify_integer_non_null(value)
        self.__AVERAGE_INI_WEIGHT = int(value)

    # Mean repetition factor
    def set_average_repetition_factor(self, value):
        """Set task's average repetition factor during the random selection of the dataflow dataflow.
        default: 5
        """        
        self.__verify_integer_non_null(value)
        self.__AVERAGE_RF = int(value)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~dataflow~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_dataflow_type(self, value):
        """

        :type value: str
        """
        self.__dataflow_TYPE = str(value)

    def set_normalized(self, value):
        """

        :type value: bool
        """
        self.__NORMALIZED = bool(value)

    def set_reentrant(self, value):
        """

        :type value: bool
        """
        self.__REENTRANT = bool(value)

    def set_multi_graph(self, value):
        """

        :type value: bool
        """
        self.__MULTI_ARC = bool(value)

    def set_acyclic(self, value):
        """

        :type value: bool
        """
        self.__ACYCLIC = bool(value)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~PRELOAD~SOLVER~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_solver(self, value):
        """Permit to choose between two solver for generate initial marking (from two sufficient conditions):
        "SC1", "SC2", "auto", "None"
        default: "auto"
        """        
        self.__SOLVER = str(value)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~PRINT~OPTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def set_logging_level(self, value):
        """Set the logging level of the generator
        default: logging.ERROR
        """
        self.__LOGGING_LEVEL = value

    def set_solver_verbose(self, value):
        """If True: GLPK will talk
        default: False
        """
        self.__VERBOSE_SOLVER = bool(value)
        
    def set_lp_filename(self, value):
        """Set the file name where the ILP of the initial marking's solver will be write
        None value By default (it will write nothing)
        """
        self.__LP_FILENAME = value

    ########################################################################
    #                           GETTERS                                    #
    ########################################################################
    # dataflow
    def get_nb_task(self):
        """Return the number of task/actors choose in parameters.
        """        
        return self.__NB_TASK

    def get_min_task_degree(self):
        """Return the minimum arcs count choose in parameters.
        """        
        return self.__MIN_TASK_DEGREE

    def get_max_task_degree(self):
        """Return the maximum arcs count choose in parameters.
        """        
        return self.__MAX_TASK_DEGREE

    # PHASES
    def get_min_phase_count(self):
        """Return the minimum phase count choose in parameters.
        """        
        return self.__MIN_PHASE_COUNT

    def get_max_phase_count(self):
        """Return the maximum phase count choose in parameters.
        """        
        return self.__MAX_PHASE_COUNT

    def get_average_time(self):
        """Return the average time choose in parameters for cyclic phases.
        """        
        return self.__AVERAGE_TIME

    # INITIAL PHASES
    def get_min_phase_count_ini(self):
        """Return the minimum initial phase count choose in parameters.
        """        
        return self.__MIN_INI_PHASE_COUNT

    def get_max_phase_count_ini(self):
        """Return the maximum initial phase count choose in parameters.
        """        
        return self.__MAX_INI_PHASE_COUNT

    def get_average_time_ini(self):
        """Return the average time choose in parameters for initial phases.
        """        
        return self.__AVERAGE__INI_TIME

    def get_average_weight_ini(self):
        """Return the average initial weight of tasks choose in parameters.
        """        
        return self.__AVERAGE_INI_WEIGHT

    # Mean repetition factor
    def get_average_repetition_factor(self):
        """Return the average repetition factor choose in parameters.
        """        
        return self.__AVERAGE_RF

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~dataflow~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_dataflow_type(self):
        """Return the type of the dataflow (SDF, CSDF, PCG)
        """        
        return self.__dataflow_TYPE

    def is_normalized(self):
        """Return True if the dataflow has at least one reentrant arc.
        """
        return self.__NORMALIZED

    def is_reentrant(self):
        """Return True if the dataflow has at least one reentrant arc.
        """
        return self.__REENTRANT

    def is_multi_arc(self):
        """Return True if the dataflow has at least one reentrant arc.
        """
        return self.__MULTI_ARC

    def is_acyclic(self):
        """Return True if the dataflow is acyclic.
        """
        return self.__ACYCLIC

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~PRELOAD~SOLVER~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_solver(self):
        """Returns the solver choose in parameters.
        :rtype : str
        """
        return self.__SOLVER

    # ~~~~~~~~~~~~~~~~~~~~~~~~~PRINT~OPTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def is_solver_verbose(self):
        """Returns the GLPK verbose option choice.
        """
        return self.__VERBOSE_SOLVER

    def get_lp_filenam(self):
        """Set the file name where the ILP of the initial marking's solver will be write.
        None value By default (it will write nothing).
        """
        return self.__LP_FILENAME
    
    def get_logging_level(self):
        """Return the logging level of the generator.
        """
        return self.__LOGGING_LEVEL
    
    @staticmethod
    def __verify_integer_non_negativ(value):
        if int(value) < 0:
            raise Exception("Wrong value: it must be positive")

    @staticmethod
    def __verify_integer_non_null(value):
        if int(value) < 1:
            raise Exception("Wrong value: it must be non null")

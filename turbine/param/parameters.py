import logging


class Error(Exception):
    pass
error = Error  # backward compatibility

class Parameters :
    """This class contains all options for generate dataflow graph
    """

    def __init__(self) :

        #~~~~~~~~~~~~~~~~~~~~~~~GENERATOR~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # GRAPH
        # Number of task in the graph
        self.__NB_TASK = 10
        # Minimum output/input arc count for the graph
        self.__MIN_ARCS_COUNT = 1
        # Maximum output/input arc count for the graph 
        self.__MAX_ARCS_COUNT = 5

        # PHASES
        # Minimum phase count for a task
        self.__MIN_PHASE_COUNT = 1
        # Maximum phase count for a task
        self.__MAX_PHASE_COUNT = 5
        # Average Time for a phase
        self.__AVERAGE_TIME = 10

        # INITIAL PHASES
        # Minimum initial phase count 
        self.__MIN_PHASE_COUNT_INIT = 0
        # Maximum initial phase count 
        self.__MAX_PHASE_COUNT_INIT = 2
        # Average Initial time for a phase
        self.__AVERAGE_TIME_INIT = 10
        
        # ARC
        #
        self.__AVERAGE_WEIGHT_INIT = 10

        # TASK
        # Average repetition factor of a task
        self.__AVERAGE_RF = 5

        #~~~~~~~~~~~~~~~~~~~~~~~GRAPH~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # dataflow has threshold's consumption phases
        self.__THRESHOLD = True
        # Dataflow has initial phases 
        self.__INITIALIZED = True
        # Dataflow has re-entrant arcs/edges
        self.__NO_REENTRANT = False

        #~~~~~~~~~~~~~~~~~~~~~PRELOAD~SOLVER~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # Select the initial marking's solver
        self.__SOLVER = "auto"
        
        #~~~~~~~~~~~~~~~~~~~~~PRINT~OPTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.__VERBOSE_GLPK = False
        self.__LOGGING_LEVEL = logging.ERROR
        # The file name where the ILP of the initial marking's solver will be write
        self.__LP_FILENAME = None
        


########################################################################
#                           SETTERS                                    #
########################################################################
    # GRAPH
    def setNbTask(self, value):
        """Set the number of task/actors of the dataflow graph.
        default : 10
        """
        self.__verifyInteger(value)
        if value < 2 :
            raise Error("Wrong value : it must be greater than 1")
        self.__NB_TASK = int(value)

    def setMinArcsCount(self, value):
        """Set the minimum arcs count during the random selection of the dataflow graph.
        default : 1
        """        
        self.__verifyInteger(value)
        self.__MIN_ARCS_COUNT = int(value)

    def setMaxArcsCount(self, value):
        """Set the maximum arcs count during the random selection of the dataflow graph.
        default : 5
        """        
        self.__verifyInteger(value)
        self.__MAX_ARCS_COUNT = int(value)

    # PHASES
    def setMinPhaseCount(self, value):
        """Set task's minimum phase count during the random selection of the dataflow graph.
        default : 1
        """
        self.__verifyInteger(value)
        self.__MIN_PHASE_COUNT = int(value)

    def setMaxPhaseCount(self, value):
        """Set task's maximum phase count during the random selection of the dataflow graph.
        default : 5
        """        
        self.__verifyInteger(value)
        self.__MAX_PHASE_COUNT = int(value)

    def setAverageTime(self, value):
        """Set phase's average time during the random selection of the dataflow graph.
        default : 10
        """        
        self.__verifyInteger(value)
        self.__AVERAGE_TIME = int(value)

    # INITIAL PHASES
    def setMinPhaseCountInit(self, value):
        """Set task's minimum initial phase count during the random selection of the dataflow graph.
        default : 0
        """        
        self.__verifyInteger(value)
        self.__MIN_PHASE_COUNT_INIT = int(value)

    def setMaxPhaseCountInit(self, value):
        """Set task's maximum phase count during the random selection of the dataflow graph.
        default : 2
        """        
        self.__verifyInteger(value)
        self.__MAX_PHASE_COUNT_INIT = int(value)

    def setAverageTimeInit(self, value):
        """Set initial phase's average time during the random selection of the dataflow graph.
        default : 10
        """        
        self.__verifyInteger(value)
        self.__AVERAGE_TIME_INIT = int(value)

    def setAverageWeightInit(self, value):
        """Set initial phase's average time during the random selection of the dataflow graph.
        default : 10
        """        
        self.__verifyInteger(value)
        self.__AVERAGE_WEIGHT_INIT = int(value)

    # Mean repetition factor
    def setAverageRepetitionFactor(self, value):
        """Set task's average repetition factor during the random selection of the dataflow graph.
        default : 5
        """        
        self.__verifyInteger(value)
        self.__AVERAGE_RF = int(value)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~GRAPH~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def setIsThreshold(self, value):
        """If True : generate dataflow with thresholds
        default : False
        """        
        self.__THRESHOLD = bool(value)

    def setIsInitialized(self, value):
        """If True : generate dataflow with initial phases 
        default : False
        """        
        self.__INITIALIZED = bool(value)

    def setIsNotReentrant(self, value):
        """If True : generate dataflow without reentrant arcs/edges 
        default : False
        """        
        self.__NO_REENTRANT = bool(value)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PRELOAD~SOLVER~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def setSolver(self, value):
        """Permit to choose between two solver for generate initial marking (from two sufficient conditions) : "SC1", "SC2", "auto"  
        default : "auto"
        """        
        self.__SOLVER = str(value)

#~~~~~~~~~~~~~~~~~~~~~~~~~~PRINT~OPTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def setLoggingLevel(self, value):
        """Set the logging level of the generator
        default : logging.ERROR
        """
        self.__LOGGING_LEVEL = value

        """If True : GLPK will talk
        default : False
        """
    def setGLPKVerbose(self, value):
        self.__VERBOSE_GLPK = bool(value)
        

    def setLPFileName(self, value):
        """Set the file name where the ILP of the initial marking's solver will be write
        None value By default (it will write nothing)
        """
        self.__LP_FILENAME = value

########################################################################
#                           GETTERS                                    #
########################################################################
    # GRAPH
    def getNbTask(self):
        """Return the number of task/actors choose in parameters.
        """        
        return self.__NB_TASK

    def getMinArcsCount(self):
        """Return the minimum arcs count choose in parameters.
        """        
        return self.__MIN_ARCS_COUNT

    def getMaxArcsCount(self):
        """Return the maximum arcs count choose in parameters.
        """        
        return self.__MAX_ARCS_COUNT

    # PHASES
    def getMinPhaseCount(self):
        """Return the minimum phase count choose in parameters.
        """        
        return self.__MIN_PHASE_COUNT

    def getMaxPhaseCount(self):
        """Return the maximum phase count choose in parameters.
        """        
        return self.__MAX_PHASE_COUNT

    def getAverageTime(self):
        """Return the average time choose in parameters for cyclic phases.
        """        
        return self.__AVERAGE_TIME

    # INITIAL PHASES
    def getMinPhaseCountInit(self):
        """Return the minimum initial phase count choose in parameters.
        """        
        return self.__MIN_PHASE_COUNT_INIT

    def getMaxPhaseCountInit(self):
        """Return the maximum initial phase count choose in parameters.
        """        
        return self.__MAX_PHASE_COUNT_INIT

    def getAverageTimeInit(self):
        """Return the average time choose in parameters for initial phases.
        """        
        return self.__AVERAGE_TIME_INIT

    def getAverageWeightInit(self):
        """Return the average initial weight of tasks choose in parameters.
        """        
        return self.__AVERAGE_WEIGHT_INIT

    # Mean repetition factor
    def getAverageRepetitionFactor(self):
        """Return the average repetition factor choose in parameters.
        """        
        return self.__AVERAGE_RF

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~GRAPH~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def isThresholded(self):
        """Return True if the dataflow has thresholded phase.
        """        
        return self.__THRESHOLD
        
    def isInitialized(self):
        """Return True if the dataflow has initialized task.
        """        
        return self.__INITIALIZED
        
    def isNotreentrant(self):
        """Return True if the graph has at least one reentrant arc.
        """
        return self.__NO_REENTRANT

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PRELOAD~SOLVER~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def getSolver(self):
        """Returns the solver choose in parameters.
        """
        return self.__SOLVER

#~~~~~~~~~~~~~~~~~~~~~~~~~~PRINT~OPTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def isGLPKVerbose(self):
        """Returns the GLPK verbose option choice.
        """
        return self.__VERBOSE_GLPK

    def getLPFileName(self):
        """Set the file name where the ILP of the initial marking's solver will be write.
        None value By default (it will write nothing).
        """
        return self.__LP_FILENAME
    
    def getLoggingLevel(self):
        """Return the logging level of the generator.
        """
        return self.__LOGGING_LEVEL
    
    def __verifyInteger(self, value):
        if int(value) < 0 :
            raise Error("Wrong value : it must be positive")

    

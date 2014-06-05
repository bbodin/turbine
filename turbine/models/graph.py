"""Interface between networkx and the generator.
"""
from algorithms.normalized import Normalized
from generation.markingComputation import generateInitialMarking
import logging

from gcd import gcdList
import networkx as nx


class Graph :
########################################################################
#                           CONSTANT                                   #
########################################################################
#--------------------------Graph---------------------------------------#
    CONST_GRAPH_NAME = "gName"
    CONST_GRAPH_PHASED = "phas"
    CONST_GRAPH_THRESHOLD = "thre"
    CONST_GRAPH_INITIALIZED = "init"
    CONST_GRAPH_REENTRANT = "reent"
    CONST_GRAPH_MULTIGRAPH = "multi"

#--------------------------Task----------------------------------------#
    CONST_TASK_NAME = "tName"
    CONST_TASK_PHASE_DURATION_LIST = "phaDurL"
    CONST_TASK_INITIAL_PHASE_DURATION_LIST = "iniPhaDurL"
    CONST_TASK_REPETITION_FACTOR = "repFac"

#--------------------------Arc-----------------------------------------#
    CONST_ARC_NAME = "aName"

    CONST_ARC_GCD = "aGcd"
    CONST_ARC_THRESHOLD_GCD = "aThGcd"
    CONST_ARC_INIT_GCD = "aInitGcd"
    CONST_ARC_INIT_THRESHOLD_GCD = "aInitThGcd"
    CONST_ARC_PRELOAD = "aPrel"
    CONST_ARC_TOKEN_SIZE = "tokS"

    CONST_ARC_CONS_LIST = "cL"
    CONST_ARC_PROD_LIST = "pL"

    CONST_ARC_CONS_THRESOLD_LIST = "cThrL"
    CONST_ARC_INI_CONS_THRESOLD_LIST = "iniCThrL"

    CONST_ARC_INI_CONS_LIST = "iniCL"
    CONST_ARC_INI_PROD_LIST = "iniPL"

    CONST_ARC_CONS_PORT_NAME = "cPN"
    CONST_ARC_PROD_PORT_NAME = "pPN"

    def __init__(self, name = "") :
        """Initialize a graph.

        Parameters
        ----------
        name : string, optional (default="")
            An optional name for the graph.
        """

        self.nxg = nx.MultiDiGraph(name = name)
        self.setName(name)
        self.__setPhased(False)
        self.__setThreshold(False)
        self.__setInitialized(False)
        self.__setReEntrant(False)
        self.__setMultigraph(False)
        
        self.taskKey = 0

        self.taskByName = {}
        self.arcByName = {}

    def __str__( self ) :
        s = "Graph name : " + self.nxg.graph[self.CONST_GRAPH_NAME] +"\n"
        return s

    def drawit(self):
        nx.draw_shell(self.nxg)

########################################################################
#                           modify graph                               #
########################################################################
    def setName(self,name):
        """Modify the graph's name.

        Parameters
        ----------
        name : the name of the graph.
        """      
        self.nxg.graph[self.CONST_GRAPH_NAME] = name

    def __setReEntrant(self, param):
        """Set the graph as reentrant.

        Parameters
        ----------
        param : a boolean.
        """
        self.nxg.graph[self.CONST_GRAPH_REENTRANT] = param

    def __setThreshold(self, param):
        """Set the graph as thresholded.

        Parameters
        ----------
        param : a boolean.
        """
        self.nxg.graph[self.CONST_GRAPH_THRESHOLD] = param

    def __setInitialized(self, param):
        """Set the graph as initialized.

        Parameters
        ----------
        param : a boolean.
        """
        self.nxg.graph[self.CONST_GRAPH_INITIALIZED] = param

    def __setPhased(self, param):
        """Set the graph as phased.

        Parameters
        ----------
        param : a boolean.
        """
        self.nxg.graph[self.CONST_GRAPH_PHASED] = param
        
    def __setMultigraph(self, param):
        """Set the graph as multigraph.

        Parameters
        ----------
        param : a boolean.
        """
        self.nxg.graph[self.CONST_GRAPH_MULTIGRAPH] = param

########################################################################
#                           add/modify task                            #
########################################################################
    def addTask(self, name=None):
        """Add a task in the graph.

        Parameters
        ----------
        name : the name of the task (default name=t+str(key of the task)).
        """
        new_task = self.taskKey
        if name == None :
            name = "t"+str(new_task)

        try :#Detect if a task with the same name exist
            self.getTaskByName(name)
            logging.error("Name already used by another task")
            return None#If it is the case the present task is not add.
        except KeyError :
            pass

        self.taskKey+=1
        self.taskByName[name] = new_task

        self.nxg.add_node(new_task)
        self.setTaskName(new_task,name)

        self.nxg.node[new_task][self.CONST_TASK_PHASE_DURATION_LIST] = [1]
        self.nxg.node[new_task][self.CONST_TASK_INITIAL_PHASE_DURATION_LIST] = []

        return new_task

    def setTaskName(self, task, name):
        """Modify the name of the task in parameters.

        Parameters
        ----------
        task : the task targeted.
        name : the name of the task.
        """
        self.nxg.node[task][self.CONST_TASK_NAME] = name
        return name

    def setRepetitionFactor (self, task, repetitionFactor):
        """Modify the repetition factor of a task.
                
        Parameters
        ----------
        task : the task targeted.
        repetitionFactor : the new repetition factor (integer).
        """

        self.nxg.node[task][self.CONST_TASK_REPETITION_FACTOR] = repetitionFactor

    def setPhaseCount (self, task, phaseCount):
        """Modify the phase count of a task and initialize the list of all connected arc's
        cyclic phase.

        Parameters
        ----------
        task : the name of the task you want modify.
        phaseCount : the number of phase of the task (integer).
        
        Note that if (and only if) the phase count is different than the previous one,
        all incidents arcs will have their cyclic weights reinitialized.
        """
        #If the number of phase is the same as before, do nothing
        if phaseCount == self.getPhaseCount(task):
            return

        if phaseCount > 1:
            self.__setPhased(True)
            
        self.nxg.node[task][self.CONST_TASK_PHASE_DURATION_LIST] = [1]*phaseCount
        
        for arc in self.getArcList(target=task):
            self.__setArcAttribute(arc,[1]*phaseCount,self.CONST_ARC_CONS_LIST)
            self.__setArcAttribute(arc,[0]*phaseCount,self.CONST_ARC_CONS_THRESOLD_LIST)

        for arc in self.getArcList(source=task):
            self.__setArcAttribute(arc,[1]*phaseCount,self.CONST_ARC_PROD_LIST)

    def setPhaseCountInit (self, task, phaseCountInit):
        """Modify the initial phase count of a task and initialize the list of all connected arc's
        initial phase.
        
        Parameters
        ----------
        task : the name of the task you want modify.
        phaseCountInit : the number of initial phase of the task (integer).
        
        Note that if (and only if) the initial phase count is different than the previous one,
        all incidents arcs will have their initial weights reinitialized.
        """
        if phaseCountInit > 0:
            self.__setInitialized(True)

        
        self.nxg.node[task][self.CONST_TASK_INITIAL_PHASE_DURATION_LIST] = [1]*phaseCountInit
        for arc in self.getArcList(target=task):
            self.__setArcAttribute(arc,[1]*phaseCountInit,self.CONST_ARC_INI_CONS_LIST)
            self.__setArcAttribute(arc,[1]*phaseCountInit,self.CONST_ARC_INI_CONS_THRESOLD_LIST)

        for arc in self.getArcList(source=task):
            self.__setArcAttribute(arc,[1]*phaseCountInit,self.CONST_ARC_INI_PROD_LIST)


    def setPhaseDuration (self, task, phase, duration):
        """Modify a phase duration of a task.
        
        Parameters
        ----------
        task : the task targeted.
        phase : the specific phase (integer).
        duration :the duration of the phase.
        """
        self.nxg.node[task][self.CONST_TASK_PHASE_DURATION_LIST][phase] = duration

    def setPhaseDurationList (self, task, phaseDurationList):
        """Modify the phase duration list of a task.
        
        Parameters
        ----------
        task : the task targeted.
        phaseDurationList : the list of phase duration of the task (integer).
        """
        self.__verifyLength(task,len(phaseDurationList))
        self.nxg.node[task][self.CONST_TASK_PHASE_DURATION_LIST] = phaseDurationList

    def setPhaseDurationInitList (self, task, iniPhaseDurationList):
        """Modify the initial phase duration list of a task.
        
        Parameters
        ----------
        task : the task targeted.
        iniPhaseDurationList : the list of initial phase duration of the task (integer).
        """
        self.__verifyLengthInit(task,len(iniPhaseDurationList))
        self.nxg.node[task][self.CONST_TASK_INITIAL_PHASE_DURATION_LIST] = iniPhaseDurationList

    def __verifyLength(self, task, lengthList):
        """Compare the length of a list and the phase number of a task.
        
        Parameters
        ----------
        task : the task targeted.
        lengthList : the size of the list.
        
        Returns:
        -------
        True if both length corresponds.
        """
        if lengthList != self.getPhaseCount(task):
            raise BaseException("On task "+str(task)+" : the length of the phase list ("+str(lengthList)+") does not match with the phase count of the task ("+str( self.getPhaseCount(task))+")")

    def __verifyLengthInit(self, task, lengthList):
        """Compare the length of a list and the initial phase number of a task.
        
        Parameters
        ----------
        task : the task targeted.
        lengthList : the size of the list.
        
        Returns:
        -------
        True if both length corresponds.
        """
        if lengthList != self.getPhaseCountInit(task):
            raise BaseException("On task "+str(task)+" : the length of the initial phase list  ("+str(lengthList)+")  does not match with the phase count of the task("+str( self.getPhaseCountInit(task))+")")

########################################################################
#                           add/modify arc                             #
########################################################################
    def addArc(self, source, target):
        """Add an arc in the graph and initialize all his list according
        to the number of phase of both tasks.

        Parameters
        ----------
        source : the name of a task you already add on the graph.
        target : the name of a task you already add on the graph.

        Return
        ------
        the tuple (source,target, key).
        """

        if len(self.getArcList(source=source, target=target))>0 :
            self.__setMultigraph(True)

        self.nxg.add_edge(source, target)
        key = self.nxg.edge[source][target].items()[-1][0]
        arc = (source,target,key)

        if self.isArcReEntrant(arc):
            self.__setReEntrant(True)

        self.setInitialMarking(arc,0)
        self.setTokenSize(arc,1)

        self.__setArcAttribute(arc,[1]*self.getPhaseCount(source),self.CONST_ARC_PROD_LIST)
        self.__setArcAttribute(arc,[1]*self.getPhaseCount(target),self.CONST_ARC_CONS_LIST)

        self.setConsPortName(arc,"cons"+str(source)+""+str(target)+""+str(key))
        self.setProdPortName(arc,"prod"+str(source)+""+str(target)+""+str(key))

        name = "a"+str(key)

        self.setArcName(arc,name)

        return arc #return the tuple (source, target, key)

    def removeArc(self,arc):
        """Remove an edge (arc of the graph.
        
        Parameters
        ----------
        arc : the arc to remove.
        """
        self.nxg.remove_edge(arc[0],arc[1],arc[2])

    def __setArcAttribute(self, arc, attrib, attribName):
        """Set a specific attribute to the arc (prelo/cPoNa/pPoNa/...).

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        attrib : (integer) the value of the attribute.
        attribName : (string) the attribute name.
        """
        self.nxg[arc[0]][arc[1]][arc[2]][attribName] = attrib

    def __setArcPhaseAttribute(self, arc, attrib, attribName, phase):#Not used
        """Set a specific attribute to the arc (prelo/cPoNa/pPoNa/...).

        Parameters
        ----------
        arc : tuple (source, destination, name).
        phase : the rank of the phase.
        attrib : (integer) the value of the attribute.
        attribName : (string) the attribute name.
        """
        self.nxg[arc[0]][arc[1]][arc[2]][attribName][phase] = attrib

    def __calcGcd(self, arc):
        """Caclulate the GCD between the consumption weight list and the
        production weight list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try :
            gcd = gcdList(self.getConsList(arc)+self.getProdList(arc))
            self.__setArcAttribute(arc,gcd, self.CONST_ARC_GCD)
        except KeyError :
            return
            
    def __calcGcdTh(self, arc):
        """Caclulate the GCD between the consumption weight list and the
        production weight list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try :
            gcd = gcdList(self.getConsThresholdList(arc))
            self.__setArcAttribute(arc,gcd, self.CONST_ARC_THRESHOLD_GCD)
        except KeyError :
            return

    def __calcGcdInit(self, arc):
        """Caclulate the GCD between the consumption weight list and the
        production weight list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try :
            if len(self.getConsInitList(arc)+self.getProdInitList(arc)) > 0 :
                gcd = gcdList(self.getConsInitList(arc)+self.getProdInitList(arc))
                self.__setArcAttribute(arc,gcd, self.CONST_ARC_INIT_GCD)
            else:
                self.__setArcAttribute(arc,1, self.CONST_ARC_INIT_GCD)
        except KeyError :
            return

    def __calcGcdInitTh(self, arc):
        """Calculate the GCD between the consumption weight list and the
        production weight list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try :
            if len(self.getConsInitThresholdList(arc)) > 0 :
                gcd = gcdList(self.getConsInitThresholdList(arc))
                self.__setArcAttribute(arc,gcd, self.CONST_ARC_INIT_THRESHOLD_GCD)
            else:
                self.__setArcAttribute(arc,1, self.CONST_ARC_INIT_THRESHOLD_GCD)

        except KeyError :
            return


    def setArcName(self, arc, name):
        """Set the name of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        name : (string) the arc name.
        """
        try :
            if self.getArcByName(name) != arc :
                logging.error("Name already used by another arc !")
                return
        except KeyError :
            pass
        
        self.__setArcAttribute(arc, str(name), self.CONST_ARC_NAME)

    def setInitialMarking(self, arc, preload):
        """Set the initial marking of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        preload : (integer) the value of the initial marking.
        """
        self.__setArcAttribute(arc, preload, self.CONST_ARC_PRELOAD)

    def setConsPortName(self, arc,consPortName):
        """Set the consumption port name of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consPortName : the name of the consumption port name.

        This is only used with the SDF3 parser.
        """
        self.__setArcAttribute(arc, consPortName, self.CONST_ARC_CONS_PORT_NAME)

    def setProdPortName(self, arc, prodPortName):
        """Set the production port name in an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        prodPortName : the name of the production port name.

        This is only used with the SDF3 parser.
        """
        self.__setArcAttribute(arc, prodPortName, self.CONST_ARC_PROD_PORT_NAME)

    def setTokenSize (self, arc, tokenSize):
        """Set the token size of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        tokenSize : the token size of this buffer/arc (integer).
        """
        self.__setArcAttribute(arc, tokenSize, self.CONST_ARC_TOKEN_SIZE)

    def setConsList(self, arc, consList):
        """Set the consumption list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consList : the list of consumption phase (integer list).
        """
        self.__verifyLength(self.getTarget(arc),len(consList))
        self.__setArcAttribute(arc, consList, self.CONST_ARC_CONS_LIST)
        self.__calcGcd(arc)

    def setConsInitList(self, arc, consInitList):
        """Set the initial consumption list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consInitList : the list of initial consumption phase (integer list).
        """
        self.__verifyLengthInit(self.getTarget(arc),len(consInitList))
        self.__setArcAttribute(arc, consInitList, self.CONST_ARC_INI_CONS_LIST)
        self.__calcGcdInit(arc)

    def setConsThresholdList(self, arc, consThresholdList):
        """Set the consumption threshold list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consThresholdList : the list of consumption threshold phase (integer list).
        """
        self.__setThreshold(True)
        self.__verifyLength(self.getTarget(arc),len(consThresholdList))
        self.__adjustThreshold(self.getConsList(arc), consThresholdList)
        self.__setArcAttribute(arc, consThresholdList, self.CONST_ARC_CONS_THRESOLD_LIST)
        self.__calcGcdTh(arc)

    def setConsInitThresholdList(self, arc, consInitThresholdList):
        """Set the initial consumption threshold list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consThresholdList : the list of initial consumption threshold
        phase (integer list).
        """    
        self.__setThreshold(True)
        self.__verifyLengthInit(self.getTarget(arc),len(consInitThresholdList))
        self.__adjustThreshold(self.getConsInitList(arc), consInitThresholdList)
        self.__setArcAttribute(arc, consInitThresholdList, self.CONST_ARC_INI_CONS_THRESOLD_LIST)
        self.__calcGcdInitTh(arc)

    def setProdList(self, arc, prodList):
        """Set the production list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consThresholdList : the list of production phase (integer list).
        """
        self.__verifyLength(self.getSource(arc),len(prodList))
        self.__setArcAttribute(arc, prodList, self.CONST_ARC_PROD_LIST)
        self.__calcGcd(arc)

    def setProdInitList(self, arc, prodInitList):
        """ Set the initial production list of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        consThresholdList : the list of initial production phase (integer list).
        """
        self.__verifyLengthInit(self.getSource(arc),len(prodInitList))
        self.__setArcAttribute(arc, prodInitList, self.CONST_ARC_INI_PROD_LIST)
        self.__calcGcdInit(arc)

    def __adjustThreshold(self, List, thresholdList):
        for i in range(0,len(List)) :
            if List[i] > thresholdList[i] :
                thresholdList[i] = List[i]


########################################################################
#                            getter graph                              #
########################################################################
    def isReEntrant(self):
        """Return True if the graph have reentrant edges.
        """
        return self.nxg.graph[self.CONST_GRAPH_REENTRANT]

    def getTaskCount(self):
        """Return the number of task of the graph.
        """
        return self.nxg.number_of_nodes()
    
    def getArcCount(self):
        """Return the number of arc of the graph.
        """
        return self.nxg.number_of_edges()
    
    def getName(self):
        """Return the name of the graph.
        """
        return self.nxg.graph[self.CONST_GRAPH_NAME]

    def isPhased (self) :
        """Return true if the graph is phased.
        """
        return self.nxg.graph[self.CONST_GRAPH_PHASED]

    def isThresholded(self) :
        """Return true if the graph has threshold.
        """
        return self.nxg.graph[self.CONST_GRAPH_THRESHOLD]

    def isInitialized(self) :
        """Return true if the graph is initialized.
        """
        return self.nxg.graph[self.CONST_GRAPH_INITIALIZED]

    def getGraphType(self):
        """Return the type of the graph : SDF/CSDF/PCG.
        """
        if not self.isThresholded() and not self.isInitialized():
            if not self.isPhased():
                return "SDFG"
            return "CSDFG"
        return "PCG"
    
    def getNormalizedGraph(self):
        if self.isNormalized():
            logging.error("Graph already normalized !")
            return self
        if 'nor' not in self.__dict__:
            self.nor = Normalized(self)
        return self.nor.getGraphNorm()
    
    def getUnNormalizedGraph(self, vector = None):
        if not self.isNormalized():
            logging.error("Graph already un-normalized !")
            return self
        if 'nor' not in self.__dict__:
            if vector == None :
                logging.error("You must specified a vector for un-normalize !")
                return
            else :
                self.nor = Normalized(self)
                return self.nor.getGraphUnNorm(self, vector)
        if vector != None :
            return self.nor.getGraphUnNorm(self, vector)
        return self.nor.getGraphUnNorm(self)
    
    def computeInitialMarking(self, solver = "auto", GLPKVerbose = False, LPFileName = None):
        generateInitialMarking(self,solver = solver, GLPKVerbose=GLPKVerbose, LPFileName=LPFileName)


########################################################################
#                            getter task                               #
########################################################################
    def getTaskList(self) :
        """Return the list of task of the graph.
        """
        return self.nxg.nodes()

    def getFirstTask(self) : 
        """Return the first (arbitrary) task of the graph.
        """
        return self.getTaskList()[0]

    def getTaskByName(self, name) :
        """Return a task according to its name.
        
        Parameters
        ----------
        name : the name of the task.
        """
        return self.taskByName[name]

    def getTaskName(self, task):
        """Return the name of a task.
        
        Parameters
        ----------
        task : the specific task.
        """
        return self.nxg.node[task][self.CONST_TASK_NAME]

    def getSuccessors(self, task):
        """Return successors of a task.
        
        Return
        ----------
        A list a successors.
        """
        return self.nxg.successors(task)

    def getPredecessors(self, task):
        """Return predecessors of a task.
        
        Return
        ----------
        A list a predecessors.
        """
        return self.nxg.predecessors(task)

    def getDegree(self, task):
        """Return degree of a task.
        
        Return
        ----------
        An integer.
        """
        return self.nxg.degree(task)

    def getInputDegree(self, task):
        """Return the input degree of a task.
        
        Return
        ----------
        An integer.
        """
        return self.nxg.in_degree(task)

    def getOutputDegree(self, task):
        """Return the output degree of a task.
        
        Return
        ----------
        An integer.
        """
        return self.nxg.out_degree(task)

    def getRepetitionFactor(self, task):
        """Return the repetition factor of a task.
        
        Return
        ----------
        An integer.
        """
        return self.nxg.node[task][self.CONST_TASK_REPETITION_FACTOR]

    def getTaskDurationStr(self, task):
        """Return task (initial and normal) phase duration list as a string.
        
        Return
        ----------
        string.
        """
        if len(self.nxg.node[task][self.CONST_TASK_PHASE_DURATION_LIST])>0:
            cyclo = str([int(i) for i in self.nxg.node[task][self.CONST_TASK_PHASE_DURATION_LIST]])[1:-1]
        if len(self.nxg.node[task][self.CONST_TASK_INITIAL_PHASE_DURATION_LIST])>0:
            init  = str([int(i) for i in self.nxg.node[task][self.CONST_TASK_INITIAL_PHASE_DURATION_LIST]])[1:-1]
            if len(init) > 0 :
                return (str(init) + ";" + str(cyclo)).replace(" ","")
            else :
                return str(cyclo).replace(" ","")
        return str(cyclo).replace(" ","")

    def getPhaseDuration(self, task):
        """Return task phase duration list.
        
        Return
        ----------
        List of integers.
        """
        return self.nxg.node[task][self.CONST_TASK_PHASE_DURATION_LIST]
        
    def getPhaseDurationInit(self, task):
        """Return task initial phase duration list.
        
        Return
        ----------
        List of integers.
        """
        return self.nxg.node[task][self.CONST_TASK_INITIAL_PHASE_DURATION_LIST]

    def getPhaseCount(self, task):
        """Return task number of phases.
        
        Return
        ----------
        An integers.
        """
        return len(self.nxg.node[task][self.CONST_TASK_PHASE_DURATION_LIST])

    def getPhaseCountInit(self, task):
        """Return task number of initial phases.
        
        Return
        ----------
        An integers.
        """
        return len(self.nxg.node[task][self.CONST_TASK_INITIAL_PHASE_DURATION_LIST])

########################################################################
#                            getter arc                                #
########################################################################
    def getArcList(self, source=None, target=None):
        """Return an arc according to parameters filled.
        
        Parameters
        ----------
        source : source task.
        target : target task.
        
        Returns
        -------
        A vector of arcs.
        
        """
        if source == None and target != None :#target is filled, the method returns all input arcs of the target
            return self.nxg.in_edges(target, keys=True)
        if source != None and target == None :#source is filled, the method returns all output arcs of the source
            return self.nxg.out_edges(source, keys=True)
        if source == None and target == None :#Nothing is filled, the method return all arcs of the graph
            return self.nxg.edges(keys = True)
        #Both source and target are filled, the method return all arcs 
        #with the source has a source and the target has a target.
        return [x for x in self.nxg.in_edges(target, keys=True) if  self.getSource(x) == source]

    def getArcByName(self, name):
        """Return an arc according to his name.
        
        Parameters
        ----------
        Name of an arc.
        
        Returns
        -------
        arc: a tuple (source, target) or (source, target, key).
        """
        return self.arcByName[name]

    def getInputArcList(self, task ) :
        """Return all input arcs of a task.
        
        Parameters
        ----------
        task.
        
        Returns
        -------
        List of arcs.
        """
        return self.nxg.in_edges(task, keys=True)

    def getOutputArcList(self, task ) :
        """Return all output arcs of a task.
        
        Parameters
        ----------
        task
        
        Returns
        -------
        List of arcs.
        """
        return self.nxg.out_edges(task, keys=True)

    def getSource(self, arc):
        """Return the source as a task of the arc.
        
        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).

        Returns
        -------
        Task source.
        """
        return arc[0]

    def getTarget(self, arc):
        """Return the target as a task of the arc.
        
        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).

        Returns
        -------
        Task target.
        """
        return arc[1]

    def isArcReEntrant(self,arc):
        """Return True if the arc is reentrant.
                
        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).
        """
        source = self.getSource(arc)
        target = self.getTarget(arc)
        return source == target

    def __getArcAttribute(self, arc, attribName):
        """Get the arc attribute with the attibute name attribName.
        
        Parameters
        ----------
        arc: a tuple (source, target) or (source, target, key).
        attribName:  the attribute name (preload/consPortName/...) (str).

        Returns
        -------
        the attribute asked.
        """
        ref = []
        try :
            ref = self.nxg[arc[0]][arc[1]][arc[2]]
        except:
            raise BaseException("Arc ref %s not found" % str(arc))
        return ref[attribName]

    def getArcName(self, arc):
        """Return the name of an arc.

        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_NAME)

    def getInitialMarking(self, arc):
        """Return the initial marking of an arc.
        .=
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_PRELOAD)

    def getTotInitialMarking(self):
        """Return the total initial marking of the graph.
        """
        ret = 0
        for arc in self.getArcList():
            ret += self.getInitialMarking(arc)
        return ret

    def getTokenSize(self, arc):
        """Return the token size of an arc (default 1).
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_TOKEN_SIZE)

    def getConsPortName(self, arc):
        """Return the consumption port name of an arc. This is used only for sdf3 files .
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_CONS_PORT_NAME)

    def getProdPortName(self, arc):
        """Return the production port name of an arc. This is used only for sdf3 files.
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_PROD_PORT_NAME)

    def getConsStr(self, arc):
        """Return a string which recapitulate of consumption vectors of an arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
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
        if self.isInitialized():
            for i in range(0, self.getPhaseCountInit(arc[1])) :
                if self.isThresholded() and len(self.getConsInitThresholdList(arc)) > 0 and self.getConsInitList(arc)[i] != self.getConsInitThresholdList(arc)[i] :
                    result+=str(int(self.getConsInitList(arc)[i]))+":"+str(int(self.getConsInitThresholdList(arc)[i]))+","
                else :
                    result+=str(int(self.getConsInitList(arc)[i]))+","
        if (len(result) > 0) :
            result = result[0:-1]+";"#del the last comma
        for i in range(0, self.getPhaseCount(arc[1])) :     
            if self.isThresholded() and  len(self.getConsThresholdList(arc)) > 0 and self.getConsList(arc)[i] != self.getConsThresholdList(arc)[i] :
                result+=str(int(self.getConsList(arc)[i]))+":"+str(int(self.getConsThresholdList(arc)[i]))+","
            else :
                result+=str(int(self.getConsList(arc)[i]))+","
        return result[0:-1]#del the last comma

    def getProdStr(self, arc):
        """Return a string which recapitulate of production vectors of an arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
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
        if self.isInitialized():
            for i in range(0, self.getPhaseCountInit(arc[0])) :
                result+=str(int(self.getProdInitList(arc)[i]))+","
        if (len(result) > 0) :
            result = result[0:-1]+";"#del the last comma
        for i in range(0, self.getPhaseCount(arc[0])) :
            result+=str(int(self.getProdList(arc)[i]))+","
        return result[0:-1]#del the last comma

    def getConsList(self, arc):
        """Return the consumption rate vector of the arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_CONS_LIST)

    def getConsInitList(self, arc):
        """Return the initial consumption rate vector of the arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        if self.isInitialized() :
            return self.__getArcAttribute(arc, self.CONST_ARC_INI_CONS_LIST)
        else :
            return []

    def getConsThresholdList(self, arc):
        """Return the threshold rate vector of the arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        if self.isThresholded() :
            return self.__getArcAttribute(arc, self.CONST_ARC_CONS_THRESOLD_LIST)
        else :
            return self.getConsList(arc)

    def getConsInitThresholdList(self, arc):
        """Return the initial threshold rate vector of the arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        if self.isInitialized() :
            if  self.isThresholded() :
                return self.__getArcAttribute(arc, self.CONST_ARC_INI_CONS_THRESOLD_LIST)
            else :
                return self.getConsInitList(arc)
        else :
            return []

    def getProdList(self, arc):
        """Return the production rate vector of the arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_PROD_LIST)

    def getProdInitList(self, arc):
        """Return the initial production rate vector of the arc. 
        
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_INI_PROD_LIST)

    def getGcd(self, arc):
        """Return greatest common divisor (gcd) of an arc.
        This gcd is calculate according to the graph type (if the graph is initialized / thresholded).
        The gcd is between :
            -consumption vector,
            -production vector,
        if the graph is initialized
            -initial production vector,
            -initial consumption vector,
        if the graph is thresholded
            -consumption threshold vector,
            -production threshold vector,
        if the graph is thresholded and initialized
            -initial consumption threshold vector,
            -initial production threshold vector.
            
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        step = self.__getGcd(arc)
        if self.isThresholded() :
            step = gcdList([step]+[self.__getGcdTh(arc)])
        if self.isInitialized() :
            step = gcdList([step]+[self.__getGcdInit(arc)])
        if self.isInitialized() and self.isThresholded() :
            step = gcdList([step]+[self.__getGcdInitTh(arc)])
        return step

    def __getGcd(self, arc):
        """Return greatest common divisor (gcd) of consumption and production 
        vectors of an arc.
            
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_GCD)

    def __getGcdInit(self, arc):
        """Return greatest common divisor (gcd) of initial consumption and 
        initial production vectors of an arc.
            
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try :
            return self.__getArcAttribute(arc, self.CONST_ARC_INIT_GCD)
        except  KeyError:
            return 0

    def __getGcdTh(self, arc):
        """Return greatest common divisor (gcd) of consumption threshold vector 
        of an arc.
            
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        return self.__getArcAttribute(arc, self.CONST_ARC_THRESHOLD_GCD)

    def __getGcdInitTh(self, arc):
        """Return greatest common divisor (gcd) of consumption initial threshold 
        vector of an arc.
            
        Parameters
        ----------
        arc : tuple (source, destination) or (source, destination, name)
            (default name=lowest unused integer).
        """
        try :
            return self.__getArcAttribute(arc, self.CONST_ARC_INIT_THRESHOLD_GCD)
        except  KeyError:
            return 0

########################################################################
#                            print & verify fonctions                  #
########################################################################
    def printInfo(self):
        """Print informations about the graph.
        """
        degreeInMoy = 0
        degreeInTot = 0
        degreeOutMoy = 0
        degreeOutTot = 0
        degreeMoy = 0

        RVTot = 0
        RVMoy = 0

        phasesTot = 0
        phasesMoy = 0

        for task in self.getTaskList():
            degreeInTot+=len(self.getArcList(target = task))
            degreeOutTot+=len(self.getArcList(source = task))

            RVTot +=self.getRepetitionFactor(task)

            phasesTot += self.getPhaseCount(task)

        degreeInMoy = degreeInTot/self.getTaskCount()
        degreeOutMoy = degreeOutTot/self.getTaskCount()
        degreeMoy = (degreeInTot + degreeOutTot)/self.getTaskCount()

        RVMoy = RVTot/self.getTaskCount()

        phasesMoy = phasesTot/self.getTaskCount()

        print "Graph : "+str(self.getName())+", Type : "+str(self.getGraphType())
        print "Normalized : "+str(self.isNormalized())+", Multigraph : "+str(self.isMultiGraph())+", reentrant : "+str(self.isReEntrant())
        print "Number of tasks : "+str(self.getTaskCount())
        print "Number of edges : "+str(self.getArcCount())
        print "Task incoming degree tot: "+str(degreeInTot)+", moy : "+str(degreeInMoy)
        print "Task outgoing degree tot: "+str(degreeOutTot)+", moy : "+str(degreeOutMoy)
        print "Task degree tot: "+str(degreeInTot + degreeOutTot)+", moy : "+str(degreeMoy)
        print "Repetition factor tot : "+str(RVTot)+", moy : "+str(RVMoy)
        print "Phases tot : "+str(phasesTot)+", moy : "+str(phasesMoy)
        print "Tot initial marking : "+str(self.getTotInitialMarking())

        

        if self.isCyclic() :
            print "Cycle detected !"
        else :
            print "No cycle"

    def isCyclic(self) :
        """Return true if the graph has cycle (reentrant arcs are not considerate as cycle).
        """
        return max(len(cc) for cc in nx.strongly_connected_components(self.nxg)) > 1

    def strTask(self, task):
        """Return a string which represent a task.
        """
        s="TASK : "+str(task)+" RF:"+str(self.getRepetitionFactor(task))+" Degree:"+str(self.getDegree(task))+" in:"+str(self.getInputDegree(task))+" out:"+str(self.getOutputDegree(task))+"\n"
        s+="\tPhase count : "+str(self.getPhaseCount(task))+" Duration : "+str(self.getPhaseDuration(task))+"\n"
        if self.isThresholded() and self.getPhaseCountInit(task) > 0 :
            s+="\tInitial phase count: "+str(self.getPhaseCountInit(task))+" Duration : "+str(self.getPhaseDurationInit(task))
        return s

    def printTasks(self):
        """Print all tasks of the graph.
        """
        for task in self.getTaskList():
            print self.strTask(task)

    def strArc(self, arc):
        """Return a string which represent an arc.
        """
        s="ARC : "+str(arc[0])+"->"+str(arc[1])+" M0:"+str(self.getInitialMarking(arc))+" Token size:"+str(self.getTokenSize(arc))+"\n"

        initProdStr = ""
        prodStr = self.getProdStr(arc).replace(".0", "")
        if ";" in prodStr :
            initProdStr, prodStr = prodStr.split(";")
            initProdStr = "("+str(initProdStr)+")"
        s+="\tProd : "+str(initProdStr)+"["+str(prodStr)+"]"
        s+="\n"
        
        initConsStr = ""
        consStr = self.getConsStr(arc).replace(".0", "")
        if ";" in consStr :
            initConsStr, consStr = consStr.split(";")
            initConsStr = "("+str(initConsStr)+")"
        s+="\tCons : "+str(initConsStr)+"["+str(consStr)+"]"
        
        return s

    def printArcs(self):
        """Print all arcs of the graph.
        """
        for arc in self.getArcList():
            print self.strArc(arc)

    def printBuffer(self):
        """Print all buffers (initial marking) of the graph.
        """
        for arc in self.getArcList():
            print str(arc)+" M0:"+str(self.getInitialMarking(arc))

    def isNormalized(self):
        """Return True if the graph is normalized.
        """
        for task in self.getTaskList() :
            if len(self.getOutputArcList(task)) > 0:
                refValue = sum(self.getProdList(self.getOutputArcList(task)[0]))
            else:
                refValue = sum(self.getConsList(self.getInputArcList(task)[0]))
                
            for arc in self.getOutputArcList(task):
                if sum(self.getProdList(arc)) !=  refValue :
                    return False 
            for arc in self.getInputArcList(task):
                if sum(self.getConsList(arc)) !=  refValue :
                    return False 
        return True

    def isMultiGraph(self):
        """Return True if the graph is has multi arc (ie more than one arc for a couple of tasks).
        """
        return self.nxg.graph[self.CONST_GRAPH_MULTIGRAPH]

    def isConsistent(self):
        """Return True if the graph is consistent.
        """
        for arc in self.getArcList():
            weighteSource = sum(self.getProdList(arc))*self.getRepetitionFactor(self.getSource(arc))
            weighteTarget = sum(self.getConsList(arc))*self.getRepetitionFactor(self.getTarget(arc))
            if weighteSource != weighteTarget :
                return False
        return True


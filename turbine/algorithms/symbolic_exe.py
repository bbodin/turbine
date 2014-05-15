from random import *
import logging
import time


class SymbolicExe :
    def __init__(self, graph):
        self.graph = graph

    #Execute the symbolic execution until the number of iteration reach self.ite
    def execute(self):
        self.__raz()
        
        numTaskExe = [0]*self.graph.getTaskCount()#execution number of the task during current step
        executedTask = [False]*self.graph.getTaskCount()#if the task can be executed
        debut = time.time()
        terminate = False#Symbolic exe succeed ?
        stepTwo = False#Engage step Two ?
        i = 0
        for task in self.graph.getTaskList():
            numTaskExe[task] = 0
        #~ print "PHASE ONE"
        while not terminate :
            
            for task in self.graph.getTaskList(): # zero executed task
                executedTask[task] = False

            # 1 - Choose which task can be execute
            taskExecute = 0
            logging.debug("iteration : "+ str(i))
            for task in self.graph.getTaskList():
                if self.__isExecutable(task):
                    executedTask[task] = True

                    #If we are in step Two
                    if stepTwo and float(numTaskExe[task])/float(self.graph.getPhaseCount(task)) == self.graph.getRepetitionFactor(task) :
                        #If the task has been executed enought then don't execute it
                        executedTask[task] = False
                        taskExecute-=1
                    if logging.getLogger().getEffectiveLevel() == logging.DEBUG :#Avoid to browse the list of arcs if not in debug
                        logging.debug("execute task : "+str(task))
                        for arc in self.graph.getInputArcList(task):
                            logging.debug("\tInput arc : "+str(arc)+" M0="+str(self.M0[arc]))
                    taskExecute+=1

            #2 - Execute tasks selected
            for task in self.graph.getTaskList():
                if executedTask[task] : #If the task is selected
                    numTaskExe[task] += 1 #Increase the number of exe of this task
                    if self.__taskExe(task) == -1: #If the execution went wrong stop the process
                        logging.error("Negative buffer, this should never occur...")
                        return -1

            #Should we go to step Two ?
            if not stepTwo :
                numExe = 0 #Number of task which has enough execution
                for task in self.graph.getTaskList():
                    if numTaskExe[task] >= self.graph.getPhaseCountInit(task)+self.graph.getPhaseCount(task) :   
#                     if numTaskExe[task] >= self.graph.getPhaseCountInit(task)+self.graph.getPhaseCount(task):
                        numExe+=1
                if numExe == self.graph.getTaskCount() :
                    logging.debug("number of exe : "+str(numTaskExe))
                    for task in self.graph.getTaskList():
                        numTaskExe[task] = 0
                    stepTwo = True
                    logging.debug("PHASE TWO ENGAGE !!! fasten your seatbelt.")

            #Step Two over ?
            if stepTwo :
                numExe = 0#Number of task which has enought execution
                for task in self.graph.getTaskList():
                    #If the number of execution of the task is more or equal to its repetition factor
                    if float(numTaskExe[task])/float(self.graph.getPhaseCount(task)) == self.graph.getRepetitionFactor(task):
                        numExe+=1
                #If all task have been executed enought the symbolic exe is successful
                if numExe == self.graph.getTaskCount():
                    terminate = True

            #If nothing append the initial marking is wrong :-(
            if taskExecute == 0 :
                logging.error("No task executed :-/, iteration : "+str(i))
                logging.error("Arcs exe : "+str(self.arcExe))
                logging.debug("number of exe : "+str(numTaskExe))
                return -1

            i+=1
        fin = time.time()
        logging.info("Symbolic execution succeed in "+str(fin-debut)+"s, with "+str(i)+" iterations")
        return 0 #Exe successful 

    #Used when __init__ is called
    #Initialized preload and phases
    #Phases are negative when the graph have initialized phases.
    def __raz(self):
        self.arcExe = 0

        self.M0 = {}
        for arc in self.graph.getArcList():
            self.M0[arc] = self.graph.getInitialMarking(arc)

        self.currentPhase = {}
        for task in self.graph.getTaskList():
            self.currentPhase[task] = 0
            if self.graph.isInitialized() :
                self.currentPhase[task] = -self.graph.getPhaseCountInit(task)

    #Execute a task : delet preload from input arcs, add preload on output arc
    #and increment the actual phase of the task
    def __taskExe(self, task):
        for inArc in self.graph.getArcList(target = task):
            self.M0[inArc] -= self.__getTokenDel(inArc)
            if self.M0[inArc] < 0 :
                return -1
            self.arcExe += 1

        for outArc in self.graph.getArcList(source = task):
            self.M0[outArc]+=self.__getTokenCreate(outArc)
            self.arcExe += 1

        self.currentPhase[task] +=1
        if self.currentPhase[task] == self.graph.getPhaseCount(task):
            self.currentPhase[task] = 0

        return 0

    #Return True if the task is executable (ie input arcs have enough initial marking)
    def __isExecutable(self,task):
        for inArc in self.graph.getArcList(target = task):
            if self.M0[inArc] < self.__getTokenNeed(inArc) :
                return False
        return True

    #Return the amount of data create on an arc depending of his production and the actual phase of the source
    def __getTokenCreate(self, outArc):
        dataCreate = 0
        task = self.graph.getSource(outArc)
        curPhase = self.currentPhase[task]
        
        if curPhase < 0 :
            dataCreate = self.graph.getProdInitList(outArc)[self.graph.getPhaseCountInit(task) + curPhase]
        else :
            dataCreate = self.graph.getProdList(outArc)[curPhase]
        return dataCreate

    #Return the amount of data del on an input arc when the target is execute.
    def __getTokenDel(self, inArc):
        dataDel = 0
        task = self.graph.getTarget(inArc)
        curPhase = self.currentPhase[task]
        
        if curPhase < 0 :
            dataDel = self.graph.getConsInitList(inArc)[self.graph.getPhaseCountInit(task) + curPhase]
        else :
            dataDel = self.graph.getConsList(inArc)[curPhase]
        return dataDel

    #return the data needed by an arc to execute the current phase of the target.
    def __getTokenNeed(self, inArc):
        dataNeed = 0
        task = self.graph.getTarget(inArc)
        curPhase = self.currentPhase[task]

        if self.graph.isThresholded() :
            if curPhase < 0 :
                dataNeed = self.graph.getConsInitThresholdList(inArc)[self.graph.getPhaseCountInit(task) + curPhase]
            else :
                dataNeed = self.graph.getConsThresholdList(inArc)[curPhase]
        else :
            return self.__getTokenDel(inArc)
        return dataNeed

    ########################################################################
    #                       Printing fonctions                             #
    ########################################################################
    #Print the actual amount of each buffer (arcs)
    def printBuffer(self):
        for arc in self.graph.getArcList():
            print str(arc)+" M0 : "+str(self.M0[arc])
        print "------------------------------"

    #Print all arc which are blocking the graph. If all task are impacted, the graph is not alive.
    def printBlockingTask(self):
        for task in self.graph.getTaskList():
            if not self.__isExecutable(task) :
                for inArc in self.graph.getArcList(target = task):
                    if self.M0[inArc] < self.__getTokenNeed(inArc):
                        print "BLOCKING ARC : "+str(inArc)+" phase : "+str(self.currentPhase[task])+" need : "+str(self.__getTokenNeed(inArc))+" buffer : "+str(self.M0[inArc])+ " STEP : "+str(self.graph.getGcd(inArc))

    #Print all task that can be executed. If None, the graph is not alive.
    def printNoBlockingTask(self):
        for task in self.graph.getTaskList():
            for inArc in self.graph.getArcList(target = task):
                if self.M0[inArc] > self.__getTokenNeed(inArc):
                    print "NO BLOCKING ARC : "+str(inArc)+" phase : "+str(self.currentPhase[task])+" need : "+str(self.__getTokenNeed(inArc))+" buffer : "+str(self.M0[inArc])+ " STEP : "+str(self.graph.getGcd(inArc))

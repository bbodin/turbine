from glpk import *
import logging


class SolverSC1 :

    def __init__(self, graph, verbose, LPFileName) :
        self.graph = graph
        self.verbose = verbose
        self.LPFileName = LPFileName

        self.colV = {}#dict use for storing gamma's variable column
        self.colM0 = {}#dict use for storing buffer's variable column 
        self.colFM0 = {}#dict use for storing FM0's variable column
        
    def generateInitialMarking(self):
        self.__initProb()#Modify parameters
        self.__createCol()#Add Col on prob
        self.__createRow()#Add Row (constraint) on prob
        self.__solveProb()#Launch the solver and set preload of the graph
        del self.prob#Del prob
        return self.Z#Return the total amount find by the solver

    def __initProb(self):#Modify parameters
        logging.info("Generating initial marking problem")
        self.prob = glp_create_prob()
        glp_set_prob_name(self.prob, "min_preload")
        glp_set_obj_dir(self.prob, GLP_MIN)

        #GLPK parameters :
        self.glpkParam = glp_smcp()
        glp_init_smcp(self.glpkParam)#Do it before modify parameters
        
        self.glpkParam.presolve = GLP_ON
        self.glpkParam.msg_lev = GLP_MSG_ALL
        if not self.verbose :
            self.glpkParam.msg_lev = GLP_MSG_ERR;
        self.glpkParam.meth = GLP_DUALP
        self.glpkParam.out_frq = 2000#consol print frequency
        #~ self.glpkParam.tm_lim =300000#time limit in millisecond (5min)

    def __createCol(self):#Add Col on prob
        #Counting column
        totPhaseCount = 0
        for task in self.graph.getTaskList():
            totPhaseCount+=self.graph.getPhaseCount(task)
            if self.graph.isInitialized() :
                totPhaseCount += self.graph.getPhaseCountInit(task)

        colCount = totPhaseCount+self.graph.getArcCount()*2
        logging.info("Number of column : "+str(colCount))

        #Create column
        glp_add_cols(self.prob, colCount)

        col=1
        #Create column buffer (M0)
        for arc in self.graph.getArcList():
            self.__addColM0(col, "M0"+str(arc), arc)
            col+=1

        #Create column buffer (FM0)
        for arc in self.graph.getArcList():
            self.__addColFM0(col, "FM0"+str(arc), arc)
            col+=1
            
        #Create column lambda (v)
        for task in self.graph.getTaskList():
            phaseCount = self.graph.getPhaseCount(task)
            if self.graph.isInitialized() :
                phaseCount += self.graph.getPhaseCountInit(task)
            for i in xrange(phaseCount):
                self.__addColV(col, str(task)+"/"+str(i))
                col+=1

    def __createRow(self):#Add Row (constraint) on prob
        #Counting row
        FRowCount = self.graph.getArcCount()
        for arc in self.graph.getArcList():
            if self.graph.isArcReEntrant(arc) :
                FRowCount -=1
                
        rowCount = 0
        for arc in self.graph.getArcList():
            source = self.graph.getSource(arc)
            target = self.graph.getTarget(arc)
            if not self.graph.isArcReEntrant(arc) :
                if self.graph.isInitialized() :
                    sourcePhaseCount = self.graph.getPhaseCount(source)+self.graph.getPhaseCountInit(source)
                    targetPhaseCount = self.graph.getPhaseCount(target)+self.graph.getPhaseCountInit(target)
                    rowCount += sourcePhaseCount * targetPhaseCount
                else :
                    rowCount += self.graph.getPhaseCount(source) * self.graph.getPhaseCount(target)

        #Create row
        logging.info("Number of rows : "+str(rowCount+FRowCount))
        glp_add_rows(self.prob, rowCount+FRowCount)

        self.varArraySize = rowCount*3 + FRowCount*2 + 1
        logging.info("Var array size : "+str(self.varArraySize))
        self.varRow = intArray(self.varArraySize)
        self.varCol = intArray(self.varArraySize)
        self.varCoef = doubleArray(self.varArraySize)

        #BEGUIN FILL ROW
        self.k = 1
        row = 1
        ########################################################################
        #                       Constraint FM0*step - M0 = 0                   #
        ########################################################################
        for arc in self.graph.getArcList():
            if not self.graph.isArcReEntrant(arc) :
                step = self.graph.getGcd(arc)
                self.__addFRow(row,arc,step)
                row+=1

        ########################################################################
        #                       Constraint u-u'+M0 >= W1+1                     #
        ########################################################################
        for arc in self.graph.getArcList():
            source = self.graph.getSource(arc)
            target = self.graph.getTarget(arc)
            if not self.graph.isArcReEntrant(arc) :
                rangeSource = self.__getRangePhases(source)
                rangeTarget = self.__getRangePhases(target)
                prodList = self.__getProdList(arc)
                consList = self.__getConsList(arc)
                if self.graph.isThresholded():
                    thresholdList = self.__getThresholdList(arc)
                step = self.graph.getGcd(arc)

                predOut = 0
                for sourcePhase in xrange(rangeSource):#source/prod/out normaux
                    if sourcePhase > 0 : predOut +=prodList[sourcePhase-1]

                    predIn = 0
                    In = 0
                    for targetPhase in xrange(rangeTarget):#target/cons/in normaux
                        In += consList[targetPhase]
                        if targetPhase > 0 : predIn += consList[targetPhase-1]

                        W1 = In - predOut - step
                        if self.graph.isThresholded():
                            W1 += predIn + thresholdList[targetPhase] - In

                        strV1 = str(source)+"/"+str(sourcePhase)
                        strV2 = str(target)+"/"+str(targetPhase)

                        self.__addRow(row,strV1,strV2,arc,W1)
                        row+=1
        #END FILL ROW

    def __solveProb(self):#Launch the solver and set preload of the graph
        logging.info("loading matrix ...")
        glp_load_matrix(self.prob, self.varArraySize-1, self.varRow, self.varCol, self.varCoef)

        if self.LPFileName != None : 
            problemLocation = str(glp_write_lp(self.prob, None, self.LPFileName))
            logging.info("Writing problem : "+str(problemLocation)) 

        logging.info("solving problem ...")
        ret = str(glp_simplex(self.prob, self.glpkParam))
        logging.info("Solver return : "+ret)

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG :
            for arc in self.graph.getArcList():
                logging.debug(str(arc)+" M0 : "+str(glp_get_col_prim(self.prob, self.colM0[arc]))+" FM0 : "+str(glp_get_col_prim(self.prob, self.colFM0[arc])))
            for arc in self.graph.getArcList():
                source = self.graph.getSource(arc)
                target = self.graph.getTarget(arc)
                for phaseS in xrange(self.__getRangePhases(source)) :
                    for phaseT in xrange(self.__getRangePhases(target)) :
                        logging.debug(str(arc)+" V"+str(source)+"/"+str(phaseS)+" : "+str(glp_get_col_prim(self.prob, self.colV[str(source)+"/"+str(phaseS)]))+" V"+str(target)+"/"+str(phaseT)+" : "+str(glp_get_col_prim(self.prob, self.colV[str(target)+"/"+str(phaseT)])))

        self.Z = glp_get_obj_val(self.prob)

        optBuffer = True
        bufRevTot = 0

        #Revision of the final buffer (in case of non integer variable)
        for arc in self.graph.getArcList():
            if not self.graph.isArcReEntrant(arc) :
                buf = glp_get_col_prim(self.prob, self.colM0[arc])
                FM0 = glp_get_col_prim(self.prob, self.colFM0[arc])
                step = self.graph.getGcd(arc)

                if FM0 % 1 == 0 :
                    self.graph.setInitialMarking(arc, int(buf))
                    bufRevTot += int(buf)

                else :
                    optBuffer = False
                    self.graph.setInitialMarking(arc, (int(FM0)+1)*step)
                    bufRevTot += (int(FM0)+1)*step
        
        logging.info("SC1 Mem tot (no reentrant) : "+str(self.Z)+" REV : "+str(bufRevTot))
        if optBuffer == True : logging.info("Solution SC1 Optimal !!")
        else : logging.info("Solution SC1 Not Optimal :-(") 

    #Add a variable lamda
    def __addColV(self,col,name):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_FR, 0, 0)
        glp_set_obj_coef(self.prob, col, 0.0)
        self.colV[name] = col

    #Add a variable M0
    def __addColM0(self, col, name, arc):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0, 0)
        glp_set_obj_coef(self.prob, col, 1.0)
        self.colM0[arc] = col

    #Add a variable FM0
    def __addColFM0(self, col, name, arc):
        glp_set_col_kind(self.prob, col, GLP_IV)
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0, 0)
        glp_set_obj_coef(self.prob, col, 0.0)
        self.colFM0[arc] = col

    #Add a constraint : lambda1 - lambda2 + M0 > W1
    def __addRow(self, row, strV1, strV2, arc, W1):
        if self.graph.getSource(arc) != self.graph.getTarget(arc) :
            self.varRow[self.k] = row
            self.varCol[self.k] = self.colV[strV1]
            self.varCoef[self.k] = 1.0
            self.k+=1

            self.varRow[self.k] = row
            self.varCol[self.k] = self.colV[strV2]
            self.varCoef[self.k] = -1.0
            self.k+=1

        self.varRow[self.k] = row
        self.varCol[self.k] = self.colM0[arc]
        self.varCoef[self.k] = 1.0
        self.k+=1

        glp_set_row_bnds(self.prob, row, GLP_LO, W1+0.000000001, 0.0)#W1+1 cause there is no strict bound with GLPK
        glp_set_row_name(self.prob, row, "r_"+str(row))

    #Add a constraint : FM0*step = M0
    def __addFRow(self, row, arc, step):
        self.varRow[self.k] = row
        self.varCol[self.k] = self.colFM0[arc]
        self.varCoef[self.k] = step
        self.k+=1

        self.varRow[self.k] = row
        self.varCol[self.k] = self.colM0[arc]
        self.varCoef[self.k] = -1.0
        self.k+=1
        
        glp_set_row_bnds(self.prob, row, GLP_FX, 0.0, 0.0)
        glp_set_row_name(self.prob, row, "step"+str(arc))

    def __getRangePhases(self,task):
        rangeTask = self.graph.getPhaseCount(task)
        if self.graph.isInitialized() :
            rangeTask += self.graph.getPhaseCountInit(task)
        return rangeTask

    def __getProdList(self,arc):
        prodList = self.graph.getProdList(arc)
        if self.graph.isInitialized() :
            prodList = self.graph.getProdInitList(arc) + prodList
        return prodList

    def __getConsList(self,arc):
        consList = self.graph.getConsList(arc)
        if self.graph.isInitialized() :
            consList =  self.graph.getConsInitList(arc) + consList
        return consList

    def __getThresholdList(self,arc):
        thresholdList = self.graph.getConsThresholdList(arc)
        if self.graph.isInitialized() :
            thresholdList = self.graph.getConsInitThresholdList(arc) + thresholdList
        return thresholdList

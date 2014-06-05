from glpk import *
import logging


class SolverSC2 :

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
        logging.info("Generating problem...")
        self.prob = glp_create_prob()
        glp_set_prob_name(self.prob, "min_preload")
        glp_set_obj_dir(self.prob, GLP_MIN)

        #GLPK parameters :
        self.parm = glp_smcp()
        glp_init_smcp(self.parm)
        self.parm.presolve = GLP_ON
        if not self.verbose :
            self.parm.msg_lev = GLP_MSG_ERR;
        self.parm.meth = GLP_DUALP
        self.parm.out_frq = 2000

    def __createCol(self):#Add Col on prob
        #Counting column
        colCount = self.graph.getArcCount()*3
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
        for arc in self.graph.getArcList():
            self.__addColV(col, "v"+str(arc))
            col+=1

    def __createRow(self):#Add Row (constraint) on prob
        #Counting row
        FRowCount = self.graph.getArcCount()
        rowCount = 0
        for task in self.graph.getTaskList():
            taskReEntrant = 0
            for arc in self.graph.getInputArcList(task):
                if self.graph.isArcReEntrant(arc) :
                    taskReEntrant+=1
            FRowCount-= taskReEntrant
            rowCount += ((self.graph.getInputDegree(task)-taskReEntrant) * (self.graph.getOutputDegree(task)-taskReEntrant))
                    
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
        #                       Constraint u-u'+M0 >= W2+1                     #
        ########################################################################
        for task in self.graph.getTaskList():
            for arcIn in self.graph.getArcList(target = task):
                if not self.graph.isArcReEntrant(arcIn) :
                    step = self.graph.getGcd(arcIn)
                    for arcOut in self.graph.getArcList(source = task):
                        if not self.graph.isArcReEntrant(arcOut) :
                            Max = self.__getMax(arcIn, arcOut)
                            
                            strV1 = "v"+str(arcIn)
                            strV2 = "v"+str(arcOut)

                            W2 = Max - step
                            self.__addRow(row, strV1, strV2, arcIn, W2)
                            row += 1
        #END FILL ROW

    def __solveProb(self):#Launch the solver and set preload of the graph
        glp_load_matrix(self.prob, self.varArraySize-1, self.varRow, self.varCol, self.varCoef)

        if self.LPFileName != None : 
            problemLocation = str(glp_write_lp(self.prob, None, self.LPFileName))
            logging.info("Writing problem : "+str(problemLocation)) 

        logging.info("solving problem ...") 
        ret = str(glp_simplex(self.prob, self.parm))
        logging.info("Solveur return : "+ret) 

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

        logging.info("SC2 Mem tot : "+str(self.Z)+" REV : "+str(bufRevTot)) 
        if optBuffer == True : logging.info("Solution SC2 Optimal !!") 
        else : logging.info("Solution SC2 Not Optimal :-(")  

    #Add a variable lamda
    def __addColV(self,col,name):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_FR, 0.0, 0.0)
        glp_set_obj_coef(self.prob, col, 0.0)
        self.colV[name] = col

    #Add a variable M0
    def __addColM0(self, col, name, arc):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0.0, 0.0)
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
    def __addRow(self, row, strV1, strV2, arc, W2):
        if strV1 != strV2 :
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

        glp_set_row_bnds(self.prob, row, GLP_LO, W2+1, 0.0)#W2+1 cause there is no strict bound with GLPK
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

    #For a couple of arcs, return the max between there in-predOut or predIn + threshold -predOut if the graph have threshold
    def __getMax(self, arcIn, arcOut):
        phaseCount = self.graph.getPhaseCount(self.graph.getTarget(arcIn))
        prodList = self.graph.getProdList(arcOut)
        consList = self.graph.getConsList(arcIn)
        thresholdList = self.graph.getConsThresholdList(arcIn)
        if self.graph.isInitialized() :
            phaseCount += self.graph.getPhaseCountInit(self.graph.getTarget(arcIn))
            prodList = self.graph.getProdInitList(arcOut) + prodList
            consList =  self.graph.getConsInitList(arcIn) + consList
            thresholdList = self.graph.getConsInitThresholdList(arcIn) + thresholdList

        retMax = self.graph.getConsList(arcIn)[0]

        predOut = 0
        predIn = 0
        In = 0
        for phase in xrange(phaseCount):
            if phase > 0 :
                predOut += prodList[phase-1]
                predIn += consList[phase-1]
            In += consList[phase]

            W2 = In - predOut
            if self.graph.isThresholded() :
                W2 += predIn + thresholdList[phase] - In

            
            if retMax < W2 : retMax = W2
        return retMax

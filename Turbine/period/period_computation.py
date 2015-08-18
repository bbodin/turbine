"""
Created on Jul 8, 2014

@author: lesparre
"""
from glpk import *
import logging


class ComputePeriod:
    def __init__(self, dataflow, verbose=False, lp_filename=None):
        logging.basicConfig(level=logging.ERROR)
        if not dataflow.is_sdf:
            raise Exception("The dataflow must be a SDF graph")
        self.dataflow = dataflow
        self.verbose = verbose
        self.lp_filename = lp_filename

        self.N = 0  # Normalised period
        self.colStart = {}  # dict use for storing task's variable column 

    def compute_period(self):
        self.__init_prob()  # Modify parameters
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        ret = self.__solve_prob()  # Launch the solver and set preload of the graph
        del self.prob  # Del prob
        return ret

    def __init_prob(self):  # Modify parameters
        logging.info("Computing period and start time")
        self.prob = glp_create_prob()
        glp_set_prob_name(self.prob, "period N start time")
        glp_set_obj_dir(self.prob, GLP_MIN)

        # GLPK parameters:
        self.glpkParam = glp_smcp()
        glp_init_smcp(self.glpkParam)  # Do it before modify parameters

        self.glpkParam.presolve = GLP_ON
        self.glpkParam.msg_lev = GLP_MSG_ALL
        if not self.verbose:
            self.glpkParam.msg_lev = GLP_MSG_ERR
        self.glpkParam.meth = GLP_DUALP
        self.glpkParam.out_frq = 2000  # consol print frequency

    def __create_col(self):  # Add Col on prob
        # Counting column
        col_count = self.dataflow.get_task_count() + 1
        logging.info("Number of column: " + str(col_count))

        # Create column
        glp_add_cols(self.prob, col_count)

        col = 1
        self.__add_col_n(col, "N")
        col += 1

        # Create column bds (M0)
        for task in self.dataflow.get_task_list():
            self.__add_col_start(col, "T" + str(task), task)
            col += 1

    def __create_row(self):  # Add Row (constraint) on prob
        # Counting row
        row_count = self.dataflow.get_arc_count()

        for arc in self.dataflow.get_arc_list():
            if self.dataflow.is_arc_reentrant(arc):
                row_count -= 1

        # Create row
        logging.info("Number of rows: " + str(row_count))
        glp_add_rows(self.prob, row_count)

        self.varArraySize = row_count * 3 + 1
        logging.info("Var array size: " + str(self.varArraySize))
        self.varRow = intArray(self.varArraySize)
        self.varCol = intArray(self.varArraySize)
        self.varCoef = doubleArray(self.varArraySize)

        # BEGUIN FILL ROW
        self.k = 1
        row = 1
        ########################################################################
        #         Constraint s(tj,1) - s(ti, 1) >= l(ti) + N(Zj - M0(p) - gcdij)#
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                source = self.dataflow.get_source(arc)
                target = self.dataflow.get_target(arc)

                m0 = self.dataflow.get_initial_marking(arc)
                if self.dataflow.is_sdf:
                    lti = self.dataflow.get_task_duration(source)
                if self.dataflow.is_csdf:
                    lti = sum(self.dataflow.get_phase_duration_list(source))
                gcd = self.dataflow.get_gcd(arc)

                if self.dataflow.is_sdf:
                    zj = self.dataflow.get_cons_rate(arc)
                if self.dataflow.is_csdf:
                    zj = sum(self.dataflow.get_cons_rate_list(arc))

                n_coef = zj - m0 - gcd
                self.__add_start_row(row, source, target, n_coef, lti)
                row += 1

    def __solve_prob(self):  # Launch the solver and set preload of the graph
        logging.info("loading matrix ...")
        glp_load_matrix(self.prob, self.varArraySize - 1, self.varRow, self.varCol, self.varCoef)

        if self.lp_filename is not None:
            problem_location = str(glp_write_lp(self.prob, None, self.lp_filename))
            logging.info("Writing problem: " + str(problem_location))

        logging.info("solving problem ...")
        ret = str(glp_simplex(self.prob, self.glpkParam))
        logging.info("Solver return: " + ret)
        #             getErrorMessage(ret)
        #         print "N:"+str(glp_get_col_prim(self.prob, self.N))
        #         print Fraction(str(glp_get_col_prim(self.prob, self.N)))
        #         for task in self.graph.get_task_list():
        #             print "start time of task "+str(task)+": "+str(glp_get_col_prim(self.prob, self.colStart[task]))
        return glp_get_col_prim(self.prob, self.N)

    #         self.Z = glp_get_obj_val(self.prob)

    # Add the variable N
    def __add_col_n(self, col, name):
        kmin = 0.0
        for task in self.dataflow.get_task_list():
            try:
                arc = self.dataflow.get_arc_list(source=task)[0]
            except IndexError:
                arc = self.dataflow.get_arc_list(target=task)[0]
            if self.dataflow.is_sdf:
                task_duration = self.dataflow.get_task_duration(task)
                prod = self.dataflow.get_prod_rate(arc)
            if self.dataflow.is_csdf:
                task_duration = sum(self.dataflow.get_phase_duration_list(task))
                prod = sum(self.dataflow.get_prod_rate_list(arc))
            kmin = max(kmin, float(task_duration) / float(prod))
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, kmin, 0)
        glp_set_obj_coef(self.prob, col, 1.0)
        self.N = col

    # Add a variable start
    def __add_col_start(self, col, name, task):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0, 0)
        self.colStart[task] = col

    # Add a constraint:
    def __add_start_row(self, row, source, target, ncoef, lti):
        self.varRow[self.k] = row
        self.varCol[self.k] = self.colStart[target]
        self.varCoef[self.k] = 1.0
        self.k += 1

        self.varRow[self.k] = row
        self.varCol[self.k] = self.colStart[source]
        self.varCoef[self.k] = -1.0
        self.k += 1

        self.varRow[self.k] = row
        self.varCol[self.k] = self.N
        self.varCoef[self.k] = float(-ncoef)
        self.k += 1

        glp_set_row_bnds(self.prob, row, GLP_LO, lti, 0.0)
        glp_set_row_name(self.prob, row, "step" + str((source, target)))

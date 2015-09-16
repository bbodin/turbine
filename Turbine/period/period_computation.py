"""
Created on Jul 8, 2014
"""
from glpk import *
import logging


class ComputePeriod:
    """
    Compute the period of the 1-periodic schedule for a SDF graph.
    """

    def __init__(self, dataflow, verbose=False, lp_filename=None):
        logging.basicConfig(level=logging.ERROR)
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        if not dataflow.is_sdf:
            raise Exception("The dataflow must be a SDF graph !")
        if not dataflow.is_normalized:
            raise Exception("The dataflow must be normalized !")

        self.dataflow = dataflow
        self.verbose = verbose
        self.lp_filename = lp_filename

        self.N = 0  # Normalised period
        self.col_start = {}  # dict use for storing task's variable column

    def compute_period(self):
        self.__init_prob()  # Modify parameters
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        ret = self.__solve_prob()  # Launch the solver and set preload of the graph
        del self.prob  # Del prob

        f_task = self.dataflow.get_task_list()[0]
        rep_v = self.dataflow.get_repetition_factor(f_task)
        try:
            z = self.dataflow.get_prod_rate(self.dataflow.get_arc_list(source=f_task)[0])
        except IndexError:
            z = self.dataflow.get_cons_rate(self.dataflow.get_arc_list(target=f_task)[0])

        return ret * z * rep_v

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

        re_entrant_arc = 0
        for arc in self.dataflow.get_arc_list():
            if self.dataflow.is_arc_reentrant(arc):
                re_entrant_arc += 1
        row_count -= re_entrant_arc

        # Create row
        logging.info("Number of rows: " + str(row_count))
        glp_add_rows(self.prob, row_count)

        self.var_array_size = (self.dataflow.get_arc_count() - re_entrant_arc) * 3 + 1
        logging.info("Var array size: " + str(self.var_array_size))
        self.var_row = intArray(self.var_array_size)
        self.var_col = intArray(self.var_array_size)
        self.var_coef = doubleArray(self.var_array_size)

        # Fill row
        self.k = 1
        row = 1
        ########################################################################
        #         Constraint s(tj,1) - s(ti, 1) >= l(ti) + N(Zj - M0(p) - gcdij)#
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                source = self.dataflow.get_source(arc)
                target = self.dataflow.get_target(arc)

                if self.dataflow.is_sdf:
                    lti = self.dataflow.get_task_duration(source)
                    zj = self.dataflow.get_cons_rate(arc)
                if self.dataflow.is_csdf:
                    lti = sum(self.dataflow.get_phase_duration_list(source))
                    zj = sum(self.dataflow.get_cons_rate_list(arc))
                gcd = self.dataflow.get_gcd(arc)
                m0 = self.dataflow.get_initial_marking(arc)

                n_coef = m0 + gcd - zj
                self.__add_start_row(row, source, target, n_coef, lti)
                row += 1

    def __solve_prob(self):  # Launch the solver and set preload of the graph
        logging.info("loading matrix ...")
        glp_load_matrix(self.prob, self.var_array_size - 1, self.var_row, self.var_col, self.var_coef)

        if self.lp_filename is not None:
            problem_location = str(glp_write_lp(self.prob, None, self.lp_filename))
            logging.info("Writing problem: " + str(problem_location))

        logging.info("solving problem ...")
        ret = str(glp_simplex(self.prob, self.glpkParam))
        logging.info("Solver return: " + ret)

        # Start date for each task
        # for task in self.dataflow.get_task_list():
        #     print "start time of task " + str(task) + " : " + str(glp_get_col_prim(self.prob, self.col_start[task]))

        return glp_get_col_prim(self.prob, self.N)

    # Add the variable N
    def __add_col_n(self, col, name):
        kmin = 0.0
        # Bound N for faster solving and handle re-entrant arc here.
        for arc in self.dataflow.get_arc_list():
            if self.dataflow.is_sdf:
                task_duration = self.dataflow.get_task_duration(self.dataflow.get_source(arc))
                cons = self.dataflow.get_cons_rate(arc)
            if self.dataflow.is_csdf:
                task_duration = sum(self.dataflow.get_phase_duration_list(self.dataflow.get_source(arc)))
                cons = sum(self.dataflow.get_cons_rate_list(arc))
            m0 = self.dataflow.get_initial_marking(arc)
            gcd = self.dataflow.get_gcd(arc)
            if cons - m0 - gcd < 0:
                kmin = min(kmin, float(task_duration) / float(cons - m0 - gcd))
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, -kmin, 0.0)
        glp_set_obj_coef(self.prob, col, 1.0)
        self.N = col

    # Add a variable start
    def __add_col_start(self, col, name, task):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0.0, 0.0)
        self.col_start[task] = col

    # Add a constraint:
    def __add_start_row(self, row, source, target, n_coef, lti):
        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_start[target]
        self.var_coef[self.k] = 1.0
        self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_start[source]
        self.var_coef[self.k] = -1.0
        self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.N
        self.var_coef[self.k] = float(n_coef)
        self.k += 1

        glp_set_row_bnds(self.prob, row, GLP_LO, lti, lti)
        glp_set_row_name(self.prob, row, "step" + str((source, target)))

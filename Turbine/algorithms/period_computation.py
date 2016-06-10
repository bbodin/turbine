"""
Created on Jul 8, 2014
"""
from fractions import gcd
import logging

from swiglpk import *


class ComputePeriod:
    """
    Compute the period of the 1-periodic schedule for a SDF graph.
    """

    def __init__(self, dataflow, verbose=False, lp_filename=None):
        logging.basicConfig(level=logging.ERROR)
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        if not dataflow.is_normalized:
            raise ValueError("The dataflow must be normalized !")

        self.dataflow = dataflow
        self.verbose = verbose
        self.lp_filename = lp_filename

        self.K = 0  # Non Normalised period
        self.col_start = {}  # dict use for storing task's variable column

    def compute_period(self):
        self.__init_prob()  # Modify parameters
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        ret = self.__solve_prob()  # Launch the solver and set preload of the graph
        glp_delete_prob(self.prob)
        glp_free_env()
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
            self.glpkParam.msg_lev = GLP_MSG_OFF
        self.glpkParam.meth = GLP_DUALP
        self.glpkParam.out_frq = 2000  # consol print frequency

    def __create_col(self):  # Add Col on prob
        # Counting column
        col_count = 1
        if self.dataflow.is_sdf:
            col_count += self.dataflow.get_task_count()
        elif self.dataflow.is_csdf:
            for task in self.dataflow.get_task_list():
                col_count += self.dataflow.get_phase_count(task)

        logging.info("Number of column: " + str(col_count))

        # Create column
        glp_add_cols(self.prob, col_count)
        col = 1
        self.__add_col_k(col, "N")
        col += 1

        # Create start column
        for task in self.dataflow.get_task_list():
            if self.dataflow.is_sdf:
                self.__add_col_start(col, "T" + str(task), task)
                col += 1
            elif self.dataflow.is_csdf:
                for i in xrange(self.dataflow.get_phase_count(task)):
                    self.__add_col_start(col, "T" + str(task) + "|" + str(i), (task, i))
                    col += 1

    def __create_row(self):  # Add Row (constraint) on prob
        # Counting row
        row_count = 0
        non_overlap = 0
        non_mono_phase = 0
        if self.dataflow.is_sdf:
            row_count = self.dataflow.get_arc_count()
            re_entrant_arc = 0
            for arc in self.dataflow.get_arc_list():
                if self.dataflow.is_arc_reentrant(arc):
                    re_entrant_arc += 1
            row_count -= re_entrant_arc
        elif self.dataflow.is_csdf:
            for arc in self.dataflow.get_arc_list():
                source = self.dataflow.get_source(arc)
                target = self.dataflow.get_target(arc)
                for i in xrange(self.dataflow.get_phase_count(source)):
                    for j in xrange(self.dataflow.get_phase_count(target)):
                        if not self.dataflow.is_arc_reentrant(arc) or (not i == j and i < j):
                            if self.__compute_amin(arc, i, j) <= self.__compute_amax(arc, i, j):
                                row_count += 1
            for task in self.dataflow.get_task_list():
                if self.dataflow.get_phase_count(task) > 1:
                    non_mono_phase += 1
                    non_overlap += self.dataflow.get_phase_count(task)

        # Create row
        logging.info("Number of rows: " + str(row_count + non_overlap))
        glp_add_rows(self.prob, row_count + non_overlap)

        self.var_array_size = row_count * 3 + non_overlap * 2 + 1
        if self.dataflow.is_csdf:
            self.var_array_size += non_mono_phase
        logging.info("Var array size: " + str(self.var_array_size))
        self.var_row = intArray(self.var_array_size)
        self.var_col = intArray(self.var_array_size)
        self.var_coef = doubleArray(self.var_array_size)

        # Fill row
        self.k = 1
        row = 1
        #####################################################################################
        # Constraint s(tj) - s(ti)     >= l(ti) + N(Zj - M0(p) - gcdij)                     # SDF
        # Constraint s(tjkj) - s(tiki) >= l(tik) + N(C(tjkj) - Ppr(tiki) - M0(a) - gcdij)   # CSDF
        #            if amax >= amin                                                        #
        #####################################################################################
        for arc in self.dataflow.get_arc_list():
            source = self.dataflow.get_source(arc)
            target = self.dataflow.get_target(arc)
            m0 = self.dataflow.get_initial_marking(arc)

            if self.dataflow.is_sdf:
                if not self.dataflow.is_arc_reentrant(arc):
                    gcd_v = self.dataflow.get_gcd(arc)
                    lti = self.dataflow.get_task_duration(source)
                    zj = self.dataflow.get_cons_rate(arc)
                    n_coef = zj - m0 - gcd_v
                    self.__add_main_row(row, source, target, n_coef, lti)
                    row += 1
            elif self.dataflow.is_csdf:
                for i in xrange(self.dataflow.get_phase_count(source)):
                    ltik = self.dataflow.get_phase_duration_list(source)[i]
                    for j in xrange(self.dataflow.get_phase_count(target)):
                        amax = self.__compute_amax(arc, i, j)
                        if self.__compute_amin(arc, i, j) <= amax:
                            if not self.dataflow.is_arc_reentrant(arc) or (not i == j and i < j):
                                self.__add_main_row(row, (source, i), (target, j), amax, ltik)
                                row += 1

        #####################################################################################
        # Constraints of non overlapping                                                    # CSDF
        #####################################################################################
        if self.dataflow.is_csdf:
            for task in self.dataflow.get_task_list():
                if self.dataflow.get_phase_count(task) > 1:
                    self.__add_non_overlap_row(row, task, self.dataflow.get_phase_count(task) - 1, 0)
                    row += 1
                    for phase in xrange(self.dataflow.get_phase_count(task) - 1):
                        self.__add_non_overlap_row(row, task, phase, phase + 1)
                        row += 1

    def __solve_prob(self):  # Launch the solver and set preload of the graph
        logging.info("loading matrix ...")
        glp_load_matrix(self.prob, self.var_array_size - 1, self.var_row, self.var_col, self.var_coef)

        if self.lp_filename is not None:
            problem_location = str(glp_write_lp(self.prob, None, self.lp_filename))
            logging.info("Writing problem: " + str(problem_location))

        logging.info("solving problem ...")
        ret = glp_simplex(self.prob, self.glpkParam)
        logging.info("Solver return: " + str(ret))
        if not ret == 0:
            raise RuntimeError("solver did not found solution")

        # Start date for each task
        f_task = self.dataflow.get_task_list()[0]
        rep_v = self.dataflow.get_repetition_factor(f_task)
        try:
            if self.dataflow.is_sdf:
                z = self.dataflow.get_prod_rate(self.dataflow.get_arc_list(source=f_task)[0])
            else:
                z = sum(self.dataflow.get_prod_rate_list(self.dataflow.get_arc_list(source=f_task)[0]))
        except IndexError:
            if self.dataflow.is_sdf:
                z = self.dataflow.get_cons_rate(self.dataflow.get_arc_list(target=f_task)[0])
            else:
                z = sum(self.dataflow.get_cons_rate_list(self.dataflow.get_arc_list(target=f_task)[0]))

        n = glp_get_col_prim(self.prob, self.K) * rep_v * z
        start_time = {}
        for task in self.dataflow.get_task_list():
            if self.dataflow.is_sdf:
                start_time[task] = glp_get_col_prim(self.prob, self.col_start[task])
            if self.dataflow.is_csdf:
                for phase in xrange(self.dataflow.get_phase_count(task)):
                    value = glp_get_col_prim(self.prob, self.col_start[(task, phase)])
                    start_time[(task, phase)] = value
        return n, start_time

    def __add_col_k(self, col, name):
        kmin = 0.0

        for task in self.dataflow.get_task_list():
            if self.dataflow.is_sdf:
                l = self.dataflow.get_task_duration(task)
                try:
                    z = self.dataflow.get_prod_rate(self.dataflow.get_arc_list(source=task)[0])
                except IndexError:
                    z = self.dataflow.get_cons_rate(self.dataflow.get_arc_list(target=task)[0])
                kmin = max(kmin, float(l) / float(z))
            else:
                try:
                    z = sum(self.dataflow.get_prod_rate_list(self.dataflow.get_arc_list(source=task)[0]))
                except IndexError:
                    z = sum(self.dataflow.get_cons_rate_list(self.dataflow.get_arc_list(target=task)[0]))
                for duration in self.dataflow.get_phase_duration_list(task):
                    kmin = max(kmin, float(duration) / float(z))

        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, kmin, 0.0)
        glp_set_obj_coef(self.prob, col, 1.0)
        self.K = col

    # Add a variable start
    def __add_col_start(self, col, name, task):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0.0, 0.0)
        self.col_start[task] = col

    # Add a constraint:
    def __add_main_row(self, row, source, target, n_coef, lti):
        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_start[target]
        self.var_coef[self.k] = 1.0
        self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_start[source]
        self.var_coef[self.k] = -1.0
        self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.K
        self.var_coef[self.k] = float(-n_coef)
        self.k += 1

        glp_set_row_bnds(self.prob, row, GLP_LO, lti, 0.0)
        if self.dataflow.is_sdf:
            glp_set_row_name(self.prob, row, "c" + "_T" + str(source) + "" + "_T" + str(target))
        if self.dataflow.is_csdf:
            ts, ps = source
            tt, pt = target
            glp_set_row_name(self.prob, row, "c" + "_T" + str(ts) + "|" + str(ps) + "" + "_T" + str(tt) + "|" + str(pt))

    # Constraint only for CSDF, the start of a phase is only after the first phase finished is job !
    def __add_non_overlap_row(self, row, task, phase_bef, phase):
        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_start[(task, phase)]
        self.var_coef[self.k] = 1.0
        self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_start[(task, phase_bef)]
        self.var_coef[self.k] = -1.0
        self.k += 1

        if phase == 0:
            try:
                if self.dataflow.is_sdf:
                    z = self.dataflow.get_prod_rate(self.dataflow.get_arc_list(source=task)[0])
                else:
                    z = sum(self.dataflow.get_prod_rate_list(self.dataflow.get_arc_list(source=task)[0]))
            except IndexError:
                if self.dataflow.is_sdf:
                    z = self.dataflow.get_cons_rate(self.dataflow.get_arc_list(target=task)[0])
                else:
                    z = sum(self.dataflow.get_cons_rate_list(self.dataflow.get_arc_list(target=task)[0]))
            self.var_row[self.k] = row
            self.var_col[self.k] = self.K
            self.var_coef[self.k] = z
            self.k += 1

        ltprk = self.dataflow.get_phase_duration_list(task)[phase_bef]
        glp_set_row_bnds(self.prob, row, GLP_LO, ltprk, 0.0)
        glp_set_row_name(self.prob, row, "c" + "_T" + str(task) + "|" + str(phase_bef) + "|" + str(phase))

    def __compute_amin(self, arc, s_phase, t_phase):  # Only for CSDF
        s1 = sum(self.dataflow.get_prod_rate_list(arc))
        s2 = sum(self.dataflow.get_cons_rate_list(arc))
        gcd_v = gcd(s1, s2)

        m0 = self.dataflow.get_initial_marking(arc)
        ha = max(0, self.dataflow.get_prod_rate_list(arc)[s_phase] - self.dataflow.get_cons_rate_list(arc)[t_phase])

        pjk = sum(self.dataflow.get_prod_rate_list(arc)[:s_phase + 1])
        cjk = sum(self.dataflow.get_cons_rate_list(arc)[:t_phase + 1])

        amin = ha + cjk - pjk - m0
        if not amin % gcd_v == 0:
            amin += (gcd_v - abs(amin % gcd_v))
        return amin

    def __compute_amax(self, arc, s_phase, t_phase):  # Only for CSDF
        s1 = sum(self.dataflow.get_prod_rate_list(arc))
        s2 = sum(self.dataflow.get_cons_rate_list(arc))
        gcd_v = gcd(s1, s2)

        m0 = self.dataflow.get_initial_marking(arc)

        pprjk = sum(self.dataflow.get_prod_rate_list(arc)[:s_phase])
        cjk = sum(self.dataflow.get_cons_rate_list(arc)[:t_phase + 1])

        amax = cjk - pprjk - m0 - 1
        amax -= abs(amax % gcd_v)
        return amax

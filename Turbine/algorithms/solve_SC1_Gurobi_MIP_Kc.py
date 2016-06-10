"""
Created on Jan 22, 2015

@author: lesparre
"""
from fractions import gcd
import os
from gurobipy import Model, GRB, LinExpr, QuadExpr
import logging


class SolveSC1GuMIPKc:
    """
    Solve the initial marking problem optimally with period constraint using Guroby (it must be install).
    
    The computation time can be quite long for big instances.
    """

    def __init__(self, graph, period, verbose, lp_filename):
        """
        Constructor
        """
        self.dataflow = graph
        self.verbose = verbose
        self.lp_filename = lp_filename

        self.k = period
        self.col_start = {}  # dict use for storing gamma's variable column
        self.col_m0 = {}  # dict use for storing bds's variable column
        self.col_fm0 = {}  # dict use for storing FM0's variable column

    def compute_initial_marking(self):
        self.__init_prob()  # Modify parameters
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        self.__create_obj()  # Add objectif function
        self.__solve_prob()  # Launch the solver and set preload of the graph
        del self.prob  # Del prob
        return self.z  # Return the total amount find by the solver

    def __init_prob(self):  # Modify parameters
        logging.info("Generating initial marking problem")
        self.prob = Model("SC1")

        # Gurobi parameters:
        if not self.verbose:
            self.prob.params.OutputFlag = 0
            try:
                os.remove("gurobi.log")
            except OSError:
                pass
        self.prob.params.Threads = 4

    def __create_col(self):  # Add Col on prob
        # Counting column

        # Create column bds (M0)
        for arc in self.dataflow.get_arc_list():
            self.__add_col_m0(arc)

        # Create column bds (FM0)
        for arc in self.dataflow.get_arc_list():
            self.__add_col_fm0(arc)

        # Create column lambda (v)
        for task in self.dataflow.get_task_list():
            if self.dataflow.is_sdf:
                phase_count = 1
                self.__add_col_start("t" + str(task), task)
            elif self.dataflow.is_csdf:
                phase_count = self.dataflow.get_phase_count(task)
                for i in xrange(phase_count):
                    self.__add_col_start("t" + str(task) + "|" + str(i), (task, i))
            if self.dataflow.is_pcg:
                phase_count += self.dataflow.get_ini_phase_count(task)

        # Integrate new variables
        self.prob.update()

    def __create_row(self):  # Add Row (constraint) on prob
        # BEGUIN FILL ROW
        ########################################################################
        #                       Constraint FM0*step - M0 = 0                   #
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                self.__add_frow(arc)

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
                    self.__add_main_row(arc, source, target, n_coef, lti)
            elif self.dataflow.is_csdf:
                for i in xrange(self.dataflow.get_phase_count(source)):
                    ltik = self.dataflow.get_phase_duration_list(source)[i]
                    for j in xrange(self.dataflow.get_phase_count(target)):
                        amax = self.__compute_amax(arc, i, j)
                        if self.__compute_amin(arc, i, j) <= amax:
                            if not self.dataflow.is_arc_reentrant(arc) or (not i == j and i < j):
                                self.__add_main_row(arc, (source, i), (target, j), amax, ltik)

        #####################################################################################
        # Constraints of non overlapping                                                    # CSDF
        #####################################################################################
        if self.dataflow.is_csdf:
            for task in self.dataflow.get_task_list():
                if self.dataflow.get_phase_count(task) > 1:
                    self.__add_non_overlap_row(task, self.dataflow.get_phase_count(task) - 1, 0)
                    for phase in xrange(self.dataflow.get_phase_count(task) - 1):
                        self.__add_non_overlap_row(task, phase, phase + 1)

    def __create_obj(self):
        obj = QuadExpr()

        for arc in self.dataflow.get_arc_list():
            obj += self.col_m0[arc]
        self.prob.setObjective(obj, GRB.MINIMIZE)

    def __solve_prob(self):  # Launch the solver and set preload of the graph
        logging.info("loading matrix ...")
        self.prob.update()

        if self.lp_filename is not None:
            problem_location = str(self.prob.write(self.lp_filename))
            logging.info("Writing problem: " + str(problem_location))

        logging.info("solving problem ...")
        self.prob.optimize()
        logging.info("Integer solving done !")

        self.z = self.prob.objVal

        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                self.dataflow.set_initial_marking(arc, int(self.col_m0[arc].x))

        logging.info("SC1 Mem tot (no reentrant): " + str(self.z))

    # Add a variable lamda
    def __add_col_start(self, name, task):
        var = self.prob.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name)
        self.col_start[task] = var

    # Add a variable M0
    def __add_col_m0(self, arc):
        var = self.prob.addVar(lb=0, vtype=GRB.INTEGER, name="M" + str(arc[0]) + "->" + str(arc[1]))
        self.col_m0[arc] = var

    # Add a variable FM0
    def __add_col_fm0(self, arc):
        var = self.prob.addVar(lb=0, vtype=GRB.INTEGER, name="M_" + str(arc[0]) + "->" + str(arc[1]))
        self.col_fm0[arc] = var

    def __add_main_row(self, arc, source, target, n_coef, lti):
        expr = LinExpr()
        expr += self.col_start[target]
        expr -= self.col_start[source]
        expr += -n_coef * self.k
        expr += self.col_m0[arc] * self.k

        name = "c" + "_T" + str(source) + "" + "_T" + str(target)
        if self.dataflow.is_csdf:
            ts, ps = source
            tt, pt = target
            name = "c" + "_T" + str(ts) + "|" + str(ps) + "" + "_T" + str(tt) + "|" + str(pt)

        self.prob.addConstr(expr, GRB.GREATER_EQUAL, lti, name=name)

    # Constraint only for CSDF, the start of a phase is only after the first phase finished is job !
    def __add_non_overlap_row(self, task, phase_bef, phase):
        expr = LinExpr()
        expr += self.col_start[(task, phase)]
        expr -= self.col_start[(task, phase_bef)]

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
            expr += z * self.k

        ltprk = self.dataflow.get_phase_duration_list(task)[phase_bef]
        name = "c" + "_T" + str(task) + "|" + str(phase_bef) + "|" + str(phase)
        self.prob.addConstr(expr, GRB.GREATER_EQUAL, ltprk, name=name)

    # Add a constraint: FM0*step = M0
    def __add_frow(self, arc):
        expr = LinExpr()
        expr += self.col_fm0[arc] * self.__get_gcd_v(arc)
        expr -= self.col_m0[arc]

        self.prob.addConstr(expr, GRB.EQUAL, 0)

    def __get_range_phases(self, task):
        if self.dataflow.is_sdf:
            return 1
        range_task = self.dataflow.get_phase_count(task)
        if self.dataflow.is_pcg:
            range_task += self.dataflow.get_ini_phase_count(task)
        return range_task

    def __get_prod_rate_list(self, arc):
        if self.dataflow.is_sdf:
            return [self.dataflow.get_prod_rate(arc)]
        prod_list = self.dataflow.get_prod_rate_list(arc)
        if self.dataflow.is_pcg:
            prod_list = self.dataflow.get_ini_prod_rate_list(arc) + prod_list
        return prod_list

    def __get_cons_rate_list(self, arc):
        if self.dataflow.is_sdf:
            return [self.dataflow.get_cons_rate(arc)]
        cons_list = self.dataflow.get_cons_rate_list(arc)
        if self.dataflow.is_pcg:
            cons_list = self.dataflow.get_ini_cons_rate_list(arc) + cons_list
        return cons_list

    def __get_threshold_list(self, arc):
        return self.dataflow.get_ini_threshold_list(arc) + self.dataflow.get_threshold_list(arc)

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

        # m0 = self.dataflow.get_initial_marking(arc)

        pprjk = sum(self.dataflow.get_prod_rate_list(arc)[:s_phase])
        cjk = sum(self.dataflow.get_cons_rate_list(arc)[:t_phase + 1])

        amax = cjk - pprjk - 1
        amax -= abs(amax % gcd_v)
        return amax

    def __get_gcd_v(self, arc):
        if self.dataflow.is_sdf:
            return self.dataflow.get_gcd(arc)
        if self.dataflow.is_csdf:
            return gcd(sum(self.dataflow.get_prod_rate_list(arc)), sum(self.dataflow.get_cons_rate_list(arc)))

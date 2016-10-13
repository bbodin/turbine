from copy import copy
import logging
import os

from gurobipy.gurobipy import GRB, Model, LinExpr, QuadExpr

try:
    from swiglpk import *
except ImportError:
    from glpk import *


class SolveSC2GuMIP:
    def __init__(self, graph, verbose, lp_filename):
        self.dataflow = graph
        self.verbose = verbose
        self.lp_filename = lp_filename

        self.col_v = {}  # dict use for storing gamma's variable column
        self.col_m0 = {}  # dict use for storing bds's variable column
        self.col_fm0 = {}  # dict use for storing FM0's variable column
        self.__init_prob()  # Initialize parameters

    def set_time_limitation(self, time):
        self.prob.params.timelimit = time

    def get_status(self):
        return self.prob.status

    def del_prob(self):
        del self.prob

    def compute_initial_marking(self):
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        self.__create_obj()  # Add objectif function
        self.__solve_prob()  # Launch the solver and set preload of the graph
        # del self.prob  # Del prob
        return self.Z  # Return the total amount find by the solver

    def __init_prob(self):  # Modify parameters
        logging.info("Generating initial marking problem")
        self.prob = Model("SC2_MIP")

        # Gurobi parameters:
        if not self.verbose:
            self.prob.params.OutputFlag = 0
            try:
                os.remove("gurobi.log")
            except OSError:
                pass
        self.prob.params.Threads = 2
        self.prob.params.intfeastol = 0.000001

    def __create_col(self):  # Add Col on prob
        # Create column bds (M0)
        for arc in self.dataflow.get_arc_list():
            self.__add_col_m0(arc)

        # Create column bds (FM0)
        for arc in self.dataflow.get_arc_list():
            self.__add_col_fm0(arc)

        # Create column lambda (v)
        for arc in self.dataflow.get_arc_list():
            self.__add_col_v("v" + str(arc))

        # Integrate new variables
        self.prob.update()

    def __create_row(self):  # Add Row (constraint) on prob
        # BEGUIN FILL ROW
        ########################################################################
        #                       Constraint FM0*step - M0 = 0                   #
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                step = self.dataflow.get_gcd(arc)
                self.__add_f_row(arc, step)

        ########################################################################
        #                       Constraint u-u'+M0 >= W2+1                     #
        ########################################################################
        for task in self.dataflow.get_task_list():
            for arc_in in self.dataflow.get_arc_list(target=task):
                if not self.dataflow.is_arc_reentrant(arc_in):
                    step = self.dataflow.get_gcd(arc_in)
                    for arc_out in self.dataflow.get_arc_list(source=task):
                        if not self.dataflow.is_arc_reentrant(arc_out):
                            max_v = self.__get_max(arc_in, arc_out)

                            str_v1 = "v" + str(arc_in)
                            str_v2 = "v" + str(arc_out)

                            w = max_v - step
                            self.__add_row(str_v1, str_v2, arc_in, w)
                            # END FILL ROW

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

        self.Z = self.prob.objVal

        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                self.dataflow.set_initial_marking(arc, int(self.col_m0[arc].x))

        logging.info("SC2 MIP Mem tot (no reentrant): " + str(self.Z))

    # Add a variable lamda
    def __add_col_v(self, name):
        var = self.prob.addVar(vtype=GRB.CONTINUOUS, name=name)
        self.col_v[name] = var

    # Add a variable M0
    def __add_col_m0(self, arc):
        var = self.prob.addVar(lb=0, vtype=GRB.INTEGER)
        self.col_m0[arc] = var

    # Add a variable FM0
    def __add_col_fm0(self, arc):
        var = self.prob.addVar(lb=0, vtype=GRB.INTEGER)
        self.col_fm0[arc] = var

    # Add a constraint: lambda1 - lambda2 + M0 > W2
    def __add_row(self, str_v1, str_v2, arc, w):
        expr = LinExpr()
        if str_v1 != str_v2:
            expr += self.col_v[str_v1]
            expr -= self.col_v[str_v2]
        expr += self.col_m0[arc]
        self.prob.addConstr(expr, GRB.GREATER_EQUAL, w + 0.00001)

    # Add a constraint: FM0*step = M0
    def __add_f_row(self, arc, step):
        expr = LinExpr()
        expr += self.col_fm0[arc] * float(step)
        expr -= self.col_m0[arc]
        self.prob.addConstr(expr, GRB.EQUAL, 0)

    # For a couple of arcs, return the max between there in-predOut or predIn + threshold - predOut
    # if the graph have threshold
    def __get_max(self, arc_in, arc_out):
        if self.dataflow.is_sdf:
            # return self.dataflow.get_cons_rate(arc_in)
            phase_count = 1
            prod_list = [self.dataflow.get_prod_rate(arc_out)]
            cons_list = [self.dataflow.get_cons_rate(arc_in)]
        if self.dataflow.is_csdf:
            phase_count = self.dataflow.get_phase_count(self.dataflow.get_target(arc_in))
            prod_list = self.dataflow.get_prod_rate_list(arc_out)
            cons_list = self.dataflow.get_cons_rate_list(arc_in)
            if self.dataflow.is_pcg:
                phase_count += self.dataflow.get_ini_phase_count(self.dataflow.get_target(arc_in))
                prod_list = self.dataflow.get_ini_prod_rate_list(arc_out) + prod_list
                cons_list = self.dataflow.get_ini_cons_rate_list(arc_in) + cons_list
                threshold_list = copy(self.dataflow.get_threshold_list(arc_in))
                threshold_list += self.dataflow.get_ini_threshold_list(arc_in)

        if self.dataflow.is_sdf:
            ret_max = self.dataflow.get_cons_rate(arc_in)
        if self.dataflow.is_csdf:
            ret_max = self.dataflow.get_cons_rate_list(arc_in)[0]

        pred_prod = 0
        pred_cons = 0
        cons = 0
        for phase in xrange(phase_count):
            if phase > 0:
                pred_prod += prod_list[phase - 1]
                pred_cons += cons_list[phase - 1]
            cons += cons_list[phase]

            w = cons - pred_prod
            if self.dataflow.is_pcg:
                w += pred_cons + threshold_list[phase] - cons

            if ret_max < w:
                ret_max = w
        return ret_max

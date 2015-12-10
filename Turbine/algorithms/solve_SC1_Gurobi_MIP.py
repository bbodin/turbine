import os
from gurobipy import Model, GRB, LinExpr, QuadExpr
import logging


class SolveSC1GuMIP:
    """
    Solve the initial marking problem optimally using Guroby (it must be install).
    
    The computation time can be quite long for big instances.
    """

    def __init__(self, dataflow, verbose, lp_filename):
        """
        Constructor
        """
        self.dataflow = dataflow
        self.verbose = verbose
        self.lp_filename = lp_filename

        self.col_v = {}  # dict use for storing gamma's variable column
        self.col_m0 = {}  # dict use for storing bds's variable column
        self.col_fm0 = {}  # dict use for storing FM0's variable column
        
    def compute_initial_marking(self):
        """launch the computation. This function return the objective value of the MILP problem
        
        The initial marking of the graph in parameter is modify.
        """
        self.__init_prob()  # Modify parameters
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        self.__create_obj()  # Add objectif function
        self.__solve_prob()  # Launch the solver and set preload of the graph
        del self.prob  # Del prob
        return self.Z  # Return the total amount find by the solver

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
            phase_count = self.__get_range_phases(task)
            for i in xrange(phase_count):
                self.__add_col_v(str(task) + "/" + str(i))

        # Integrate new variables
        self.prob.update()

    def __create_row(self):  # Add Row (constraint) on prob
        # BEGUIN FILL ROW
        ########################################################################
        #                       Constraint FM0*step - M0 = 0                   #
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                arc_gcd = self.dataflow.get_gcd(arc)
                self.__add_frow(arc, arc_gcd)

        ########################################################################
        #                       Constraint u-u'+M0 >= W1+1                     #
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            source = self.dataflow.get_source(arc)
            target = self.dataflow.get_target(arc)
            if not self.dataflow.is_arc_reentrant(arc):
                range_source = self.__get_range_phases(source)
                range_target = self.__get_range_phases(target)
                prod_list = self.__get_prod_rate_list(arc)
                cons_list = self.__get_cons_rate_list(arc)
                if self.dataflow.is_pcg:
                    threshold_list = self.__get_threshold_list(arc)
                arc_gcd = self.dataflow.get_gcd(arc)

                pred_prod = 0
                for sourcePhase in xrange(range_source):  # source/prod/out normaux
                    if sourcePhase > 0:
                        pred_prod += prod_list[sourcePhase - 1]

                    pred_cons = 0
                    cons = 0
                    for targetPhase in xrange(range_target):  # target/cons/in normaux
                        cons += cons_list[targetPhase]
                        if targetPhase > 0:
                            pred_cons += cons_list[targetPhase - 1]

                        w = cons - pred_prod - arc_gcd
                        if self.dataflow.is_pcg:
                            w += pred_cons + threshold_list[targetPhase] - cons

                        str_v1 = str(source) + "/" + str(sourcePhase)
                        str_v2 = str(target) + "/" + str(targetPhase)

                        self.__add_row(str_v1, str_v2, arc, w)
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

        logging.info("SC1 Mem tot (no reentrant): " + str(self.Z))

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

    # Add a constraint: lambda1 - lambda2 + M0 > W1
    def __add_row(self, str_v1, str_v2, arc, w):
        expr = LinExpr()
        if not self.dataflow.is_arc_reentrant(arc):
            expr += self.col_v[str_v1]
            expr -= self.col_v[str_v2]
        expr += self.col_m0[arc]

        self.prob.addConstr(expr, GRB.GREATER_EQUAL, w + 1)

    # Add a constraint: FM0*step = M0
    def __add_frow(self, arc, step):
        expr = LinExpr()
        expr += self.col_fm0[arc]*float(step)
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


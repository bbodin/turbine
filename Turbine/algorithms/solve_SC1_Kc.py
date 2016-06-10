import logging

try:
    from swiglpk import *
except ImportError:
    from glpk import *


class SolverSC1Kc:
    """Solve the initial marking under maximal period constraint. The period constraint is a upper bound.
    
    Small value of the period may not work.
    
    This algorithm work only for SDFG !
    """

    def __init__(self, dataflow, period, verbose, lp_filename):
        self.dataflow = dataflow
        self.verbose = verbose
        self.lp_filename = lp_filename

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
        self.K = period / z / rep_v
        self.colV = {}  # dict use for storing gamma's variable column
        self.col_m0 = {}  # dict use for storing bds's variable column
        self.col_fm0 = {}  # dict use for storing FM0's variable column

    def compute_initial_marking(self):
        self.__init_prob()  # Modify parameters
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        self.__solve_prob()  # Launch the solver and set preload of the graph
        glp_delete_prob(self.prob)
        glp_free_env()
        del self.prob  # Del prob
        return self.Z  # Return the total amount find by the solver

    def __init_prob(self):  # Modify parameters
        logging.info("Generating initial marking problem")
        self.prob = glp_create_prob()
        glp_set_prob_name(self.prob, "min_preload")
        glp_set_obj_dir(self.prob, GLP_MIN)

        # GLPK parameters:
        self.glpk_param = glp_smcp()
        glp_init_smcp(self.glpk_param)  # Do it before modify parameters

        self.glpk_param.presolve = GLP_ON
        self.glpk_param.msg_lev = GLP_MSG_ALL
        if not self.verbose:
            self.glpk_param.msg_lev = GLP_MSG_OFF
        self.glpk_param.meth = GLP_DUALP
        self.glpk_param.out_frq = 2000  # consol print frequency

    def __create_col(self):  # Add Col on prob
        # Counting column
        tot_phase_count = 0
        for task in self.dataflow.get_task_list():
            if self.dataflow.is_sdf:
                tot_phase_count = self.dataflow.get_task_count()
            if self.dataflow.is_csdf:
                tot_phase_count += self.dataflow.get_phase_count(task)
            if self.dataflow.is_pcg:
                tot_phase_count += self.dataflow.get_ini_phase_count(task)

        col_count = tot_phase_count + self.dataflow.get_arc_count() * 2
        logging.info("Number of column: " + str(col_count))

        # Create column
        glp_add_cols(self.prob, col_count)

        col = 1
        # Create column bds (M0)
        for arc in self.dataflow.get_arc_list():
            self.__add_col_m0(col, "M0" + str(arc), arc)
            col += 1

        # Create column bds (FM0)
        for arc in self.dataflow.get_arc_list():
            self.__add_col_fm0(col, "FM0" + str(arc), arc)
            col += 1

        # Create column lambda (v)
        for task in self.dataflow.get_task_list():
            phase_count = 0
            if self.dataflow.is_sdf:
                phase_count = 1
            elif self.dataflow.is_csdf:
                phase_count = self.dataflow.get_phase_count(task)
            if self.dataflow.is_pcg:
                phase_count += self.dataflow.get_ini_phase_count(task)
            for i in xrange(phase_count):
                self.__add_col_v(col, str(task) + "/" + str(i))
                col += 1

    def __create_row(self):  # Add Row (constraint) on prob
        # Counting row
        f_row_count = self.dataflow.get_arc_count()
        for arc in self.dataflow.get_arc_list():
            if self.dataflow.is_arc_reentrant(arc):
                f_row_count -= 1

        row_count = 0
        for arc in self.dataflow.get_arc_list():
            source = self.dataflow.get_source(arc)
            target = self.dataflow.get_target(arc)
            if not self.dataflow.is_arc_reentrant(arc):
                if self.dataflow.is_sdf:
                    row_count += 1
                if self.dataflow.is_csdf and not self.dataflow.is_pcg:
                    row_count += self.dataflow.get_phase_count(source) * self.dataflow.get_phase_count(target)
                if self.dataflow.is_pcg:
                    source_phase_count = self.dataflow.get_phase_count(source) \
                        + self.dataflow.get_ini_phase_count(source)
                    target_phase_count = self.dataflow.get_phase_count(target) \
                        + self.dataflow.get_ini_phase_count(target)
                    row_count += source_phase_count * target_phase_count

        # Create row
        logging.info("Number of rows: " + str(row_count + f_row_count))
        glp_add_rows(self.prob, row_count + f_row_count)

        self.var_array_size = row_count * 3 + f_row_count * 2 + 1
        logging.info("Var array size: " + str(self.var_array_size))
        self.var_row = intArray(self.var_array_size)
        self.var_col = intArray(self.var_array_size)
        self.var_coef = doubleArray(self.var_array_size)

        # BEGIN FILL ROW
        self.k = 1
        row = 1
        ########################################################################
        #                       Constraint FM0*step - M0 = 0                   #
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                step = self.dataflow.get_gcd(arc)
                self.__add_frow(row, arc, step)
                row += 1

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
                step = self.dataflow.get_gcd(arc)

                pred_prod = 0
                for source_phase in xrange(range_source):  # source/prod/out
                    if source_phase > 0:
                        pred_prod += prod_list[source_phase - 1]

                    pred_cons = 0
                    cons = 0
                    for target_phase in xrange(range_target):  # target/cons/in
                        cons += cons_list[target_phase]
                        if target_phase > 0:
                            pred_cons += cons_list[target_phase - 1]

                        w = cons - pred_prod - step
                        if self.dataflow.is_pcg:
                            w += pred_cons + threshold_list[target_phase] - cons
                        w *= self.K
                        if self.dataflow.is_sdf:
                            w += self.dataflow.get_task_duration(source)
                        elif self.dataflow.is_csdf:
                            w += self.dataflow.get_phase_duration_list(source)[source_phase]
                        str_v1 = str(source) + "/" + str(source_phase)
                        str_v2 = str(target) + "/" + str(target_phase)

                        self.__add_row(row, str_v1, str_v2, arc, w)
                        row += 1
                        # END FILL ROW

    def __solve_prob(self):  # Launch the solver and set preload/initial marking of the graph
        logging.info("loading matrix ...")
        glp_load_matrix(self.prob, self.var_array_size - 1, self.var_row, self.var_col, self.var_coef)

        if self.lp_filename is not None:
            problem_location = str(glp_write_lp(self.prob, None, self.lp_filename))
            logging.info("Writing problem: " + str(problem_location))

        logging.info("solving problem ...")
        ret = glp_simplex(self.prob, self.glpk_param)
        logging.info("Solver return: " + str(ret))

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            for arc in self.dataflow.get_arc_list():
                logging.debug(str(arc) + " M0: " + str(glp_get_col_prim(self.prob, self.col_m0[arc])) + " FM0: " +
                              str(glp_get_col_prim(self.prob, self.col_fm0[arc])))
            for arc in self.dataflow.get_arc_list():
                source = self.dataflow.get_source(arc)
                target = self.dataflow.get_target(arc)
                for phase_s in xrange(self.__get_range_phases(source)):
                    for phase_t in xrange(self.__get_range_phases(target)):
                        logging.debug(str(arc) + " V" + str(source) + "/" + str(phase_s) + ": " +
                                      str(glp_get_col_prim(self.prob, self.colV[str(source) + "/" + str(phase_s)])) +
                                      " V" + str(target) + "/" + str(phase_t) + ": " +
                                      str(glp_get_col_prim(self.prob, self.colV[str(target) + "/" + str(phase_t)])))

        self.Z = glp_get_obj_val(self.prob)

        opt_buffer = True
        buf_rev_tot = 0

        # Revision of the final bds (in case of non integer variable)
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                buf = glp_get_col_prim(self.prob, self.col_m0[arc])
                fm0 = glp_get_col_prim(self.prob, self.col_fm0[arc])
                step = self.dataflow.get_gcd(arc)

                if fm0 % 1 == 0:
                    self.dataflow.set_initial_marking(arc, int(buf))
                    buf_rev_tot += int(buf)

                else:
                    opt_buffer = False
                    self.dataflow.set_initial_marking(arc, int((int(fm0) + 1) * step))
                    buf_rev_tot += (int(fm0) + 1) * step

        logging.info("SC1 Mem tot (no reentrant): " + str(self.Z) + " REV: " + str(buf_rev_tot))
        if opt_buffer:
            logging.info("Solution SC1 Optimal !!")
        else:
            logging.info("Solution SC1 Not Optimal:-(")

    # Add a variable lamda
    def __add_col_v(self, col, name):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_FR, 0, 0)
        glp_set_obj_coef(self.prob, col, 0.0)
        self.colV[name] = col

    # Add a variable M0
    def __add_col_m0(self, col, name, arc):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0, 0)
        glp_set_obj_coef(self.prob, col, 1.0)
        self.col_m0[arc] = col

    # Add a variable FM0
    def __add_col_fm0(self, col, name, arc):
        glp_set_col_kind(self.prob, col, GLP_IV)
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0, 0)
        glp_set_obj_coef(self.prob, col, 0.0)
        self.col_fm0[arc] = col

    # Add a constraint: lambda1 - lambda2 + M0 > W1
    def __add_row(self, row, str_v1, str_v2, arc, w):
        if self.dataflow.get_source(arc) != self.dataflow.get_target(arc):
            self.var_row[self.k] = row
            self.var_col[self.k] = self.colV[str_v1]
            self.var_coef[self.k] = 1.0
            self.k += 1

            self.var_row[self.k] = row
            self.var_col[self.k] = self.colV[str_v2]
            self.var_coef[self.k] = -1.0
            self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_m0[arc]
        self.var_coef[self.k] = self.K
        self.k += 1

        glp_set_row_bnds(self.prob, row, GLP_LO, w + 1.0, 0.0)  # W1+1 cause there is no strict bound with GLPK
        glp_set_row_name(self.prob, row, "r_" + str(row))

    # Add a constraint: FM0*step = M0
    def __add_frow(self, row, arc, step):
        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_fm0[arc]
        self.var_coef[self.k] = float(step)
        self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_m0[arc]
        self.var_coef[self.k] = -1.0
        self.k += 1

        glp_set_row_bnds(self.prob, row, GLP_FX, 0.0, 0.0)
        glp_set_row_name(self.prob, row, "step" + str(arc))

    def __get_range_phases(self, task):
        if self.dataflow.is_sdf:
            return 1
        range_task = self.dataflow.get_phase_count(task)
        if self.dataflow.is_pcg:
            range_task += self.dataflow.get_ini_phase_count(task)
        return range_task

    def __get_prod_rate_list(self, arc):
        prod_list = None
        if self.dataflow.is_sdf:
            prod_list = [self.dataflow.get_prod_rate(arc)]
        if self.dataflow.is_csdf:
            prod_list = self.dataflow.get_prod_rate_list(arc)
        if self.dataflow.is_pcg:
            prod_list = self.dataflow.get_ini_prod_rate_list(arc) + prod_list
        return prod_list

    def __get_cons_rate_list(self, arc):
        cons_list = None
        if self.dataflow.is_sdf:
            cons_list = [self.dataflow.get_cons_rate(arc)]
        if self.dataflow.is_csdf:
            cons_list = self.dataflow.get_cons_rate_list(arc)
        if self.dataflow.is_pcg:
            cons_list = self.dataflow.get_ini_cons_rate_list(arc) + cons_list
        return cons_list

    def __get_threshold_list(self, arc):
        return self.dataflow.get_ini_threshold_list(arc) + self.dataflow.get_threshold_list(arc)

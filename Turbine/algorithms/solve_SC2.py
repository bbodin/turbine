import logging

from glpk import *


class SolverSC2:

    def __init__(self, graph, verbose, lp_filename):
        self.dataflow = graph
        self.verbose = verbose
        self.lp_filename = lp_filename
        
        self.colv = {}  # dict use for storing gamma's variable column
        self.col_m0 = {}  # dict use for storing bds's variable column
        self.col_fm0 = {}  # dict use for storing FM0's variable column

    def compute_initial_marking(self):
        self.__init_prob()  # Modify parameters
        self.__create_col()  # Add Col on prob
        self.__create_row()  # Add Row (constraint) on prob
        self.__solve_prob()  # Launch the solver and set preload of the graph
        del self.prob  # Del prob
        return self.Z  # Return the total amount find by the solver
        
    def __init_prob(self):  # Modify parameters
        logging.info("Generating problem...")
        self.prob = glp_create_prob()
        glp_set_prob_name(self.prob, "min_preload")
        glp_set_obj_dir(self.prob, GLP_MIN)

        # GLPK parameters:
        self.glpkParam = glp_smcp()
        glp_init_smcp(self.glpkParam)
        self.glpkParam.presolve = GLP_ON
        if not self.verbose:
            self.glpkParam.msg_lev = GLP_MSG_ERR
        self.glpkParam.meth = GLP_DUALP
        self.glpkParam.out_frq = 2000

    def __create_col(self):  # Add Col on prob
        # Counting column
        col_count = self.dataflow.get_arc_count() * 3
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
        for arc in self.dataflow.get_arc_list():
            self.__add_col_v(col, "v" + str(arc))
            col += 1

    def __create_row(self):  # Add Row (constraint) on prob
        # Counting row
        f_row_count = self.dataflow.get_arc_count()
        row_count = 0
        for task in self.dataflow.get_task_list():
            task_reentrant = 0
            for arc in self.dataflow.get_arc_list(target=task):
                if self.dataflow.is_arc_reentrant(arc):
                    task_reentrant += 1
            f_row_count -= task_reentrant
            row_count += (
                (self.dataflow.get_input_degree(task) - task_reentrant) *
                (self.dataflow.get_output_degree(task) - task_reentrant))
                    
        # Create row
        logging.info("Number of rows: " + str(row_count + f_row_count))
        glp_add_rows(self.prob, row_count + f_row_count)

        self.var_array_size = row_count * 3 + f_row_count * 2 + 1
        logging.info("Var array size: " + str(self.var_array_size))
        self.var_row = intArray(self.var_array_size)
        self.var_col = intArray(self.var_array_size)
        self.var_coef = doubleArray(self.var_array_size)

        # BEGUIN FILL ROW
        self.k = 1
        row = 1
        ########################################################################
        #                       Constraint FM0*step - M0 = 0                   #
        ########################################################################
        for arc in self.dataflow.get_arc_list():
            if not self.dataflow.is_arc_reentrant(arc):
                step = self.dataflow.get_gcd(arc)
                self.__add_f_row(row, arc, step)
                row += 1

        ########################################################################
        #                       Constraint u-u'+M0 >= W2+1                     #
        ########################################################################
        for task in self.dataflow.get_task_list():
            for arc_in in self.dataflow.get_arc_list(target=task):
                if not self.dataflow.is_arc_reentrant(arc_in):
                    step = self.dataflow.get_gcd(arc_in)
                    for arcOut in self.dataflow.get_arc_list(source=task):
                        if not self.dataflow.is_arc_reentrant(arcOut):
                            max_v = self.__get_max(arc_in, arcOut)
                            
                            str_v1 = "v" + str(arc_in)
                            str_v2 = "v" + str(arcOut)

                            w = max_v - step
                            self.__add_row(row, str_v1, str_v2, arc_in, w)
                            row += 1
        # END FILL ROW

    def __solve_prob(self):  # Launch the solver and set preload of the graph
        glp_load_matrix(self.prob, self.var_array_size - 1, self.var_row, self.var_col, self.var_coef)

        if self.lp_filename is not None:
            problem_location = str(glp_write_lp(self.prob, None, self.lp_filename))
            logging.info("Writing problem: " + str(problem_location))

        logging.info("solving problem ...") 
        ret = str(glp_simplex(self.prob, self.glpkParam))
        logging.info("Solveur return: " + ret) 

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
                    self.dataflow.set_initial_marking(arc, int((fm0 + 1) * step))
                    buf_rev_tot += int(fm0 + 1) * step

        logging.info("SC2 Mem tot: " + str(self.Z) + " REV: " + str(buf_rev_tot))
        if opt_buffer:
            logging.info("Solution SC2 Optimal !!")
        else:
            logging.info("Solution SC2 Not Optimal:-(")

    # Add a variable lamda
    def __add_col_v(self, col, name):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_FR, 0.0, 0.0)
        glp_set_obj_coef(self.prob, col, 0.0)
        self.colv[name] = col

    # Add a variable M0
    def __add_col_m0(self, col, name, arc):
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0.0, 0.0)
        glp_set_obj_coef(self.prob, col, 1.0)
        self.col_m0[arc] = col

    # Add a variable FM0
    def __add_col_fm0(self, col, name, arc):
        glp_set_col_kind(self.prob, col, GLP_CV)
        glp_set_col_name(self.prob, col, name)
        glp_set_col_bnds(self.prob, col, GLP_LO, 0, 0)
        glp_set_obj_coef(self.prob, col, 0.0)
        self.col_fm0[arc] = col

    # Add a constraint: lambda1 - lambda2 + M0 > W1
    def __add_row(self, row, str_v1, str_v2, arc, w):
        if str_v1 != str_v2:
            self.var_row[self.k] = row
            self.var_col[self.k] = self.colv[str_v1]
            self.var_coef[self.k] = 1.0
            self.k += 1

            self.var_row[self.k] = row
            self.var_col[self.k] = self.colv[str_v2]
            self.var_coef[self.k] = -1.0
            self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_m0[arc]
        self.var_coef[self.k] = 1.0
        self.k += 1

        glp_set_row_bnds(self.prob, row, GLP_LO, w + 0.00001, 0.0)  # W2+1 cause there is no strict bound with GLPK
        glp_set_row_name(self.prob, row, "r_" + str(row))

    # Add a constraint: FM0*step = M0
    def __add_f_row(self, row, arc, step):
        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_fm0[arc]
        self.var_coef[self.k] = int(step)
        self.k += 1

        self.var_row[self.k] = row
        self.var_col[self.k] = self.col_m0[arc]
        self.var_coef[self.k] = -1.0
        self.k += 1
        
        glp_set_row_bnds(self.prob, row, GLP_FX, 0.0, 0.0)
        glp_set_row_name(self.prob, row, "step" + str(arc))

    # For a couple of arcs, return the max between there in-predOut or predIn + threshold - predOut
    # if the graph have threshold
    def __get_max(self, arc_in, arc_out):
        if self.dataflow.is_sdf:
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
                threshold_list = self.dataflow.get_threshold_list(arc_in)
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

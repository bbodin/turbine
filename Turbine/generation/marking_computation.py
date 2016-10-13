import logging

from Turbine.algorithms.solve_SC1 import SolverSC1
from Turbine.algorithms.solve_SC1_Kc import SolverSC1Kc
from Turbine.algorithms.solve_SC2 import SolverSC2


########################################################################
#                           generate preload                           #
########################################################################
def compute_initial_marking(dataflow, solver_str="Auto", solver_verbose=False, lp_filename=None, period=None):
    """Step 3
    """
    coef_vector = None
    if not dataflow.is_normalized:
        coef_vector = dataflow.normalized()

    dataflow.del_initial_marking()
    if solver_str == "None" or solver_str is None:
        return

    elif solver_str == "Auto":
        if period is not None:
            solver = SolverSC1Kc(dataflow, float(period), solver_verbose, lp_filename)
            logging.info("choose solver SC1 Kc")
        elif __cs2_row_count(dataflow) < __sc1_row_count(dataflow):
            solver = SolverSC2(dataflow, solver_verbose, lp_filename)
            logging.info("choose solver SC2")
        else:
            solver = SolverSC1(dataflow, solver_verbose, lp_filename)
            logging.info("choose solver SC1")

    elif solver_str == "SC2":
        solver = SolverSC2(dataflow, solver_verbose, lp_filename)
    elif solver_str == "SC1":
        solver = SolverSC1(dataflow, solver_verbose, lp_filename)
        if period is not None:
            solver = SolverSC1Kc(dataflow, period, solver_verbose, lp_filename)

    elif solver_str == "SC1_MIP":
        from Turbine.algorithms.solve_SC1_Gurobi_MIP import SolveSC1GuMIP
        from Turbine.algorithms.solve_SC1_Gurobi_MIP_Kc import SolveSC1GuMIPKc
        solver = SolveSC1GuMIP(dataflow, solver_verbose, lp_filename)
        if period is not None:
            solver = SolveSC1GuMIPKc(dataflow, period, solver_verbose, lp_filename)
    elif solver_str == "SC2_MIP":
        from Turbine.algorithms.solve_SC2_Gurobi_MIP import SolveSC2GuMIP
        solver = SolveSC2GuMIP(dataflow, solver_verbose, lp_filename)
        if period is not None:
            raise RuntimeError("SC2_MIP with period constraints is not implemented yet.")
    else:
        raise RuntimeError("Wrong solver argument: no solver called.")

    logging.info("Generating initial marking")
    solver.compute_initial_marking()

    m0tot = __calc_reentrant(dataflow)
    logging.info("Mem tot (reentrant): " + str(m0tot))
    del solver

    if coef_vector is not None:
        dataflow.un_normalized(coef_vector)


def __cs2_row_count(dataflow):
    f_row_count = dataflow.get_arc_count()
    row_count = 0
    for task in dataflow.get_task_list():
        reentrant_task_count = 0
        for arc in dataflow.get_arc_list(target=task):
            if dataflow.is_arc_reentrant(arc):
                reentrant_task_count += 1
        f_row_count -= reentrant_task_count
        row_count += ((dataflow.get_input_degree(task) - reentrant_task_count) * (dataflow.get_output_degree(task)))
        row_count -= reentrant_task_count
    return row_count + f_row_count


def __sc1_row_count(dataflow):
    row_count = 0
    for arc in dataflow.get_arc_list():
        source = dataflow.get_source(arc)
        target = dataflow.get_target(arc)
        if not dataflow.is_arc_reentrant(arc):
            if dataflow.is_sdf:
                row_count += 1
            if dataflow.is_csdf:
                row_count += dataflow.get_phase_count(source) * dataflow.get_phase_count(target)
            if dataflow.is_pcg:
                source_phase_count = dataflow.get_phase_count(source) + dataflow.get_ini_phase_count(source)
                target_phase_count = dataflow.get_phase_count(target) + dataflow.get_ini_phase_count(target)
                row_count += source_phase_count * target_phase_count
    return row_count


def __compute_reentrant_initial_marking(dataflow):
    m0tot = 0
    for arc in dataflow.get_arc_list():
        if dataflow.is_arc_reentrant(arc):
            cons = dataflow.get_cons_rate_list(arc)
            if dataflow.is_pcg:
                cons += dataflow.get_ini_cons_rate_list(arc)

            step = dataflow.get_gcd(arc)
            m0 = sum(cons) - step

            if m0 % step != 0 or m0 == 0:
                m0 += (step - m0 % step)

            dataflow.set_initial_marking(arc, m0)
            m0tot += m0
            logging.debug("Reentrant initial marking for arc: " + str(arc) + ": " + str(m0))
    return m0tot


def __calc_reentrant(dataflow):
    m0_tot = 0
    for arc in dataflow.get_arc_list():
        if dataflow.is_arc_reentrant(arc):
            if dataflow.is_sdf:
                phase_count = 1
                prod_list = [dataflow.get_prod_rate(arc)]
                cons_list = [dataflow.get_cons_rate(arc)]
            if dataflow.is_csdf:
                phase_count = dataflow.get_phase_count(dataflow.get_target(arc))
                prod_list = dataflow.get_prod_rate_list(arc)
                cons_list = dataflow.get_cons_rate_list(arc)
            if dataflow.is_pcg:
                phase_count += dataflow.get_ini_phase_count(dataflow.get_target(arc))
                prod_list = dataflow.get_ini_prod_rate_list(arc) + prod_list
                cons_list = dataflow.get_ini_cons_rate_list(arc) + cons_list
                threshold_list = dataflow.get_ini_threshold_list(arc) + dataflow.get_threshold_list(arc)

            ret_max = cons_list[0]

            pred_out = 0
            pred_in = 0
            in_v = 0
            for phase in xrange(phase_count):
                if phase > 0:
                    pred_out += prod_list[phase - 1]
                    pred_in += cons_list[phase - 1]
                in_v += cons_list[phase]

                w = in_v - pred_out
                if dataflow.get_dataflow_type() == "PCG":
                    w += pred_in + threshold_list[phase] - in_v

                if ret_max < w:
                    ret_max = w
                dataflow.set_initial_marking(arc, ret_max)
                m0_tot += ret_max
                logging.debug("Reentrant initial marking for arc: " + str(arc) + ": " + str(ret_max))

    return m0_tot

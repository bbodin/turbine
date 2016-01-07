from fractions import gcd
from Turbine.calc.lcm import lcm
from random import shuffle, randint, sample
import logging

import numpy


def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur.

    Parameters
    ----------
    n : The size of the random list return.
    total : The sum of the list return
    """
    if total < n:
        x = [0] * (n - total) + [1] * total
        shuffle(x)
        return x

    dividers = sample(xrange(total), n - 1)
    dividers.sort()
    return [int(a - b) for a, b in zip(dividers + [total], [0] + dividers)]


########################################################################
#                           generate weight                            #
########################################################################
def generate_rates(dataflow, c_param):
    """The weight generation step of the generator (step 2)
    """
    __generate_rv(dataflow, c_param)  # generate the repetition vector
    __generate_rates(dataflow, c_param)  # generate weight vectors
    if dataflow.is_pcg:
        __generate_threshold_lists(dataflow)
        __generate_initial_phase_lists(dataflow, c_param)  # generate initial vectors


def __generate_rv(dataflow, c_param):
    """Generate the vector of repetition factor RV with gcd(RV) = 1 and SUM(RV)=sumRV
    """
    logging.info("Generate repetition vector")
    sum_rv = c_param.get_average_repetition_factor() * dataflow.get_task_count()  # Sum of the repetition vector

    gcd_value = 0

    n = dataflow.get_task_count()
    div = numpy.random.exponential(0.25)
    div = n + int(div * n)
    rv_list = numpy.random.multinomial(sum_rv, numpy.ones(n) / div)
    __get_non_zero_list(rv_list)

    # Modify the two last integers of the list to get a gcd equal to 1
    if gcd_value != 1:
        logging.info("recalculate GCD")
        while reduce(gcd, [gcd_value, rv_list[-1], rv_list[-2]]) != 1:
            rv_list[-1] -= 1
            rv_list[-2] += 1

    shuffle(rv_list)
    for task in dataflow.get_task_list():
        dataflow.set_repetition_factor(task, rv_list[task])
    return


def __generate_rates(dataflow, c_param):
    """Generate weights of the dataflow.
    """
    logging.info("Generate task wight")
    k = 0

    lcm_value = 1
    for task in dataflow.get_task_list():
        lcm_value = lcm(lcm_value, dataflow.get_repetition_factor(task))

    for task in dataflow.get_task_list():
        zi = lcm_value / dataflow.get_repetition_factor(task)
        if zi == 0:
            logging.fatal("lcmValue" + str(lcm_value))
            logging.fatal("null rate when generating, this Exception should never occur...")
            raise Exception("__generate_phase_lists",
                            "null rate when generating, this Exception should never occur...")

        if dataflow.is_sdf:
            duration = randint(1, c_param.get_average_time() * 2 - 1)
            dataflow.set_task_duration(task, duration)
            for arc in dataflow.get_arc_list(source=task):
                dataflow.set_prod_rate(arc, zi)
            for arc in dataflow.get_arc_list(target=task):
                dataflow.set_cons_rate(arc, zi)
        if dataflow.is_csdf:
            phase_count = randint(c_param.get_min_phase_count(), c_param.get_max_phase_count())
            phase_duration_list = constrained_sum_sample_pos(
                phase_count, randint(1, c_param.get_average_time() * phase_count * 2 - 1))
            __get_non_zero_list(phase_duration_list)

            dataflow.set_phase_count(task, phase_count)
            dataflow.set_phase_duration_list(task, phase_duration_list)

            for arc in dataflow.get_arc_list(source=task):
                prod_list = constrained_sum_sample_pos(phase_count, zi)
                dataflow.set_prod_rate_list(arc, prod_list)
                if sum(dataflow.get_prod_rate_list(arc)) != zi:
                    logging.fatal("constrained_sum_sample_pos return wrong list, "
                                  "it's generally cause by too large number.")
                    raise Exception("__generate_phase_lists constrained_sum_sample_pos return wrong list, "
                                    "it's generally cause by too large number.")

            for arc in dataflow.get_arc_list(target=task):
                cons_list = constrained_sum_sample_pos(phase_count, zi)
                dataflow.set_cons_rate_list(arc, cons_list)
                if sum(dataflow.get_cons_rate_list(arc)) != zi:
                    raise Exception("__generate_phase_lists constrained_sum_sample_pos return wrong list, "
                                    "it's generally cause by too large number.")

        if dataflow.get_task_count() > 1000 and k % 1000 == 0:
            logging.info(str(k) + "/" + str(dataflow.get_task_count()) + " tasks weigth generation complete.")
        k += 1


def __generate_threshold_lists(dataflow):
    for arc in dataflow.get_arc_list():
        phase_count = dataflow.get_phase_count(dataflow.get_target(arc))
        zi = sum(dataflow.get_cons_rate_list(arc))
        threshold_list = constrained_sum_sample_pos(phase_count, zi)
        dataflow.set_threshold_list(arc, threshold_list)


def __generate_initial_phase_lists(dataflow, c_param):
    """Generate initial weights of the dataflow.
    """
    if c_param.get_max_phase_count_ini() == 0:
        for task in dataflow.get_task_list():
            dataflow.set_ini_phase_count(task, 0)
            dataflow.set_ini_phase_duration_list(task, [])
        for arc in dataflow.get_arc_list():
            dataflow.set_ini_prod_rate_list(arc, [])
            dataflow.set_ini_cons_rate_list(arc, [])
        return

    logging.info("Generate initial task phase list")
    k = 0
    for task in dataflow.get_task_list():
        phase_count_init = randint(c_param.get_min_phase_count_ini(), c_param.get_max_phase_count_ini())
        if phase_count_init == 0:
            dataflow.set_ini_phase_count(task, phase_count_init)
            dataflow.set_ini_phase_duration_list(task, [])
            for arc in dataflow.get_arc_list(source=task):
                dataflow.set_ini_prod_rate_list(arc, [])
            for arc in dataflow.get_arc_list(target=task):
                dataflow.set_ini_cons_rate_list(arc, [])
            continue
        phase_duration_ini_list = constrained_sum_sample_pos(
            phase_count_init, randint(1, c_param.get_average_time_ini() * phase_count_init * 2 - 1))
        __get_non_zero_list(phase_duration_ini_list)
        dataflow.set_ini_phase_count(task, phase_count_init)
        dataflow.set_ini_phase_duration_list(task, phase_duration_ini_list)

        # ~ iniZi = gaussRandomSelection(phaseCountInit,c_param.getMAX_INIT_TOT_WEIGHT())
        ini_zi = randint(1, c_param.get_average_weight_ini() * phase_count_init - 1)

        for arc in dataflow.get_arc_list(source=task):
            ini_prod_list = constrained_sum_sample_pos(phase_count_init, ini_zi)
            dataflow.set_ini_prod_rate_list(arc, ini_prod_list)

        for arc in dataflow.get_arc_list(target=task):
            cons_ini_list = constrained_sum_sample_pos(phase_count_init, ini_zi)
            dataflow.set_ini_cons_rate_list(arc, cons_ini_list)
            if dataflow.is_pcg:
                cons_ini_threshold_list = constrained_sum_sample_pos(phase_count_init, ini_zi)
                dataflow.set_ini_threshold_list(arc, cons_ini_threshold_list)

        if dataflow.get_task_count() > 1000 and k % 1000 == 0:
            logging.info(str(k) + "/" + str(dataflow.get_task_count()) + " tasks initial weigth generation complete.")
        k += 1


def __get_non_zero_list(random_list):
    for i in xrange(len(random_list)):  # A modifier
        if random_list[i] == 0:
            rang = 0
            go = True
            try:
                while go:
                    if random_list[rang] > 1:
                        random_list[rang] -= 1
                        go = False
                    rang += 1
            except IndexError:
                pass
            random_list[i] += 1

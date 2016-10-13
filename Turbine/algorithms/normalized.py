from fractions import Fraction
from math import ceil
from numpy.random.mtrand import randint
from Turbine.calc.lcm import lcm


def normalized_dataflow(dataflow, coef_vector=None):
    """Normalize a dataflow and return the coefficient vector to un-normalized it.

    Return
    ------
    :return the un-normalize graph.
    """
    if not dataflow.is_consistent:
        raise RuntimeError("Dataflow must be consistent to be normalized")
    if dataflow.is_normalized:
        return

    if coef_vector is None:
        coef_vector = get_normalized_vector(dataflow)

    for arc in dataflow.get_arc_list():
        multiply_arc(dataflow, arc, coef_vector[arc])

    for arc in dataflow.get_arc_list():
        coef_vector[arc] = Fraction(numerator=1, denominator=coef_vector[arc])
    return coef_vector


def un_normalized_dataflow(dataflow, coef_vector=None):
    """Un-normalize according to a coefficient vector.
    """
    if not dataflow.is_normalized:
        return

    if coef_vector is not None:
        if not __test_coef_vector(dataflow, coef_vector):
            raise Exception("Coefficient vector specified is not valid !")
    else:
        coef_vector = get_rdm_un_normalized_vector(dataflow)

    for arc in dataflow.get_arc_list():
        multiply_arc(dataflow, arc, coef_vector[arc])


def multiply_arc(dataflow, arc, coef):
    if not __test_coef(coef, [dataflow.get_initial_marking(arc)]):
        dataflow.set_initial_marking(arc, int(ceil(dataflow.get_initial_marking(arc) * coef)))
    else:
        dataflow.set_initial_marking(arc, int(dataflow.get_initial_marking(arc) * coef))

    if dataflow.is_sdf:
        dataflow.set_prod_rate(arc, int(dataflow.get_prod_rate(arc) * coef))
        dataflow.set_cons_rate(arc, int(dataflow.get_cons_rate(arc) * coef))
    if dataflow.is_csdf:
        dataflow.set_prod_rate_list(arc, [int(x * coef) for x in dataflow.get_prod_rate_list(arc)])
        dataflow.set_cons_rate_list(arc, [int(x * coef) for x in dataflow.get_cons_rate_list(arc)])
    if dataflow.is_pcg:
        dataflow.set_ini_prod_rate_list(arc, [int(x * coef) for x in dataflow.get_ini_prod_rate_list(arc)])
        dataflow.set_ini_cons_rate_list(arc, [int(x * coef) for x in dataflow.get_ini_cons_rate_list(arc)])
        dataflow.set_threshold_list(arc, [int(x * coef) for x in dataflow.get_threshold_list(arc)])
        dataflow.set_ini_threshold_list(arc, [int(x * coef) for x in dataflow.get_ini_threshold_list(arc)])


def get_normalized_vector(dataflow):
    """Compute the normalization vector of an un-normalize graph.

    Return
    ------
    Return the the vector of coefficient for normalize the graph.
    """
    coef_list = {}

    lcm_rf = 1
    lcm_post_mult = 1
    for task in dataflow.get_task_list():
        lcm_rf = lcm(lcm_rf, dataflow.get_repetition_factor(task))
    for arc in dataflow.get_arc_list():
        if dataflow.is_sdf:
            rate = dataflow.get_prod_rate(arc)
        if dataflow.is_csdf:
            rate = sum(dataflow.get_prod_rate_list(arc))
        zi = lcm_rf / dataflow.get_repetition_factor(dataflow.get_source(arc))
        # print lcm_rf, "t"+str(dataflow.get_source(arc)), dataflow.get_repetition_factor(dataflow.get_source(arc))
        # print str(arc[0])+"->"+str(arc[1]), "zi", zi, "rate", rate, "ka", Fraction(numerator=zi, denominator=rate)
        coef_list[arc] = Fraction(numerator=zi, denominator=rate)
        if dataflow.is_csdf:
            for phase in dataflow.get_prod_rate_list(arc) + dataflow.get_cons_rate_list(arc):
                if float(coef_list[arc]) * float(phase) != int(coef_list[arc] * phase):
                    lcm_post_mult = lcm(lcm_post_mult, coef_list[arc].denominator)
    for arc in dataflow.get_arc_list():
        coef_list[arc] *= lcm_post_mult
    return coef_list


def get_rdm_un_normalized_vector(dataflow, max_num=10):
    """Compute the smallest vector for un-normalized the graph.

    ------
    Return the the vector of coefficient for un-normalize the graph.
    """
    if not dataflow.is_normalized:
        return

    coef = {}
    for arc in dataflow.get_arc_list():
        random_num = randint(1, max_num)
        coef[arc] = Fraction(numerator=random_num, denominator=dataflow.get_gcd(arc))
    return coef


def __test_coef_vector(dataflow, coef_vector):
    if len(coef_vector) != len(dataflow.get_arc_list()):
        return False

    for arc in dataflow.get_arc_list():
        coef = coef_vector[arc]

        if dataflow.is_sdf:
            if not __test_coef(coef, [dataflow.get_prod_rate(arc)]):
                return False
            if not __test_coef(coef, [dataflow.get_cons_rate(arc)]):
                return False

        if dataflow.is_csdf:
            if not __test_coef(coef, dataflow.get_prod_rate_list(arc)):
                return False
            if not __test_coef(coef, dataflow.get_cons_rate_list(arc)):
                return False

        if dataflow.is_pcg:
            if not __test_coef(coef, dataflow.get_ini_prod_rate_list(arc)):
                return False
            if not __test_coef(coef, dataflow.get_ini_cons_rate_list(arc)):
                return False
            if not __test_coef(coef, dataflow.get_threshold_list(arc)):
                return False
            if not __test_coef(coef, dataflow.get_ini_threshold_list(arc)):
                return False
        return True


def __test_coef(coef, coef_list):
    for x in coef_list:
        if int(x) * coef != int(int(x) * coef):
            return False
    return True

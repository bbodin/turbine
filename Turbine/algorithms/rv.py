from fractions import Fraction
import sys

from Turbine.calc.lcm import *

sys.setrecursionlimit(10000)  # 10000 is an example, try with different values


def calc_fractions_connected_actors(dataflow, fractions, a, rate_period):
    """This class is used to compute repetition vector of a graph.
    """

    fraction_a = fractions[a]

    if fraction_a == Fraction(0, 1):
        return False

    for c in dataflow.get_arc_list(source=a) + dataflow.get_arc_list(target=a):
        src = dataflow.get_source(c)
        dest = dataflow.get_target(c)
        if src == a:
            b = dest
        else:
            b = src

        if dataflow.is_sdf:
            rate_a = dataflow.get_prod_rate(c) * rate_period
            rate_b = dataflow.get_cons_rate(c) * rate_period
        if dataflow.is_csdf:
            rate_a = sum(dataflow.get_prod_rate_list(c)) * (rate_period / dataflow.get_phase_count(src))
            rate_b = sum(dataflow.get_cons_rate_list(c)) * (rate_period / dataflow.get_phase_count(dest))

        if dest == a:
            tmp = rate_b
            rate_b = rate_a
            rate_a = tmp
        if rate_a == 0 or rate_b == 0:
            print "rateA == 0 || rateB == 0"
            return False

        ratio_ab = Fraction(rate_a, rate_b)
        fraction_b = fraction_a * ratio_ab

        known_fraction_b = fractions[b]

        if known_fraction_b != Fraction(0, 1) and fraction_b != known_fraction_b:
            return False

        elif known_fraction_b == Fraction(0, 1):

            fractions[b] = fraction_b
            calc_fractions_connected_actors(dataflow, fractions, b, rate_period)
            if fractions[b] == Fraction(0, 1):
                return False

    return True


def calc_repetition_vector(g, fractions, rate_period):
    repetition_vector = {}
    l = 1

    for v in g.get_task_list():
        l = lcm(l, fractions[v].denominator)

    if l == 0:
        print("Zero vector ?")
        raise ValueError

    for v in g.get_task_list():
        repetition_vector[v] = (fractions[v].numerator * l) / fractions[v].denominator

    legcd = repetition_vector[g.get_task_list()[0]]

    for v in g.get_task_list():
        legcd = gcd(legcd, repetition_vector[v])

    if legcd <= 0:
        raise ValueError

    for v in g.get_task_list():
        repetition_vector[v] = repetition_vector[v] / legcd

    for v in g.get_task_list():
        repetition_vector[v] = repetition_vector[v] * rate_period

    return repetition_vector


def check_repetition_vector(dataflow):
    fractions = {}
    for v in dataflow.get_task_list():
        fractions[v] = Fraction(0, 1)

    rate_period = 1

    for c in dataflow.get_arc_list():
        if dataflow.is_csdf:
            rate_period = lcm(rate_period, dataflow.get_phase_count(dataflow.get_source(c)))
            rate_period = lcm(rate_period, dataflow.get_phase_count(dataflow.get_target(c)))

    if rate_period <= 0:
        raise ValueError

    for v in dataflow.get_task_list():
        if fractions[v] == Fraction(0, 1):
            fractions[v] = Fraction(1, 1)
            if not calc_fractions_connected_actors(dataflow, fractions, v, rate_period):
                return False

    repetition_vector = calc_repetition_vector(dataflow, fractions, rate_period)

    legcd = repetition_vector[dataflow.get_task_list()[0]] / dataflow.get_phase_count(dataflow.get_task_list()[0])

    for v in dataflow.get_task_list():
        legcd = gcd(legcd, repetition_vector[v] / dataflow.get_phase_count(v))

    for v in dataflow.get_task_list():
        print"%s \t: %d\tx %d \t = %d VS %d" % (dataflow.get_task_name(v),
                                                repetition_vector[v] / dataflow.get_phase_count(v),
                                                dataflow.get_phase_count(v), repetition_vector[v],
                                                dataflow.get_repetition_factor(v))
        if (dataflow.get_repetition_factor(v)) != repetition_vector[v] / (dataflow.get_phase_count(v) * legcd):
            print "error"
        else:
            print ""
    return True


def compute_rep_vect(dataflow):
    fractions = {}
    for v in dataflow.get_task_list():
        fractions[v] = Fraction(0, 1)

    rate_period = 1

    for c in dataflow.get_arc_list():
        if dataflow.is_csdf:
            rate_period = lcm(rate_period, dataflow.get_phase_count(dataflow.get_source(c)))
            rate_period = lcm(rate_period, dataflow.get_phase_count(dataflow.get_target(c)))

    if rate_period <= 0:
        raise ValueError

    for v in dataflow.get_task_list():
        if fractions[v] == Fraction(0, 1):
            fractions[v] = Fraction(1, 1)
            if not calc_fractions_connected_actors(dataflow, fractions, v, rate_period):
                return False

    repetition_vector = calc_repetition_vector(dataflow, fractions, rate_period)

    gcd_v = repetition_vector[dataflow.get_task_list()[0]]
    if dataflow.is_csdf:
        gcd_v = gcd_v / dataflow.get_phase_count(dataflow.get_task_list()[0])

    for v in dataflow.get_task_list():
        if dataflow.is_sdf:
            gcd_v = gcd(gcd_v, repetition_vector[v])
        if dataflow.is_csdf:
            gcd_v = gcd(gcd_v, repetition_vector[v] / dataflow.get_phase_count(v))

    rep_fact_list = []
    for v in dataflow.get_task_list():
        if dataflow.is_sdf:
            rep_fact = repetition_vector[v] / gcd_v
        if dataflow.is_csdf:
            rep_fact = repetition_vector[v] / (dataflow.get_phase_count(v) * gcd_v)
        dataflow.set_repetition_factor(v, rep_fact)
        rep_fact_list.append(rep_fact)
    return rep_fact_list

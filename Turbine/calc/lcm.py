from fractions import gcd


def lcm(a, b):
    return abs(a * b) / gcd(a, b)


def lcm_list(l):
    lcm_v = l[0]
    for i in l[1:]:
        lcm_v = lcm(i, lcm_v)
    return lcm_v

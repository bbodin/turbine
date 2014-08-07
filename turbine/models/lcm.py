from gcd import gcd


def lcm (a, b):
    return abs(a * b) // gcd(a, b)

def lcmList(l):
    lcmValue = l[0]
    for i in l:
        lcmValue = lcm(i, lcmValue)
    return lcmValue

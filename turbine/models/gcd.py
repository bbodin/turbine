def gcd(a,b):
    """return the PGCD between two integer.

    Parameters
    ----------
    a,b : two integer.

    Returns
    -------
    the pgcd between the two integer
    """
    while b<>0 :
        a,b=b,a%b
    return a

def gcdList(l):
    """return the PGCD of a list.

    Parameter
    ----------
    l : list of integers.

    Returns
    -------
    the pgcd between the integer of the list
    """
    gcdValue = l[0]

    for i in l:
        gcdValue = gcd(i,gcdValue)
    return gcdValue

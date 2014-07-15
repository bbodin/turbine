from fractions import Fraction
from generation.generate import generate
from models.lcm import *
import sys
sys.setrecursionlimit(10000) # 10000 is an example, try with different values



def calcFractionsConnectedActors(g,fractions,a,ratePeriod) :
    """This class is used to compute repetition vector of a graph.
    """

    fractionA = fractions[a]

    if fractionA == Fraction(0,1) :
        return False

    for c in g.getArcList(source=a) + g.getArcList(target=a) :
        src  = g.getSource(c)
        dest = g.getTarget(c)
        if (src==a) : 
            b = dest
        else :
            b = src
        rateA = sum(g.getProdList(c)) 
        rateA = rateA * (ratePeriod / g.getPhaseCount(src))
        rateB =  sum(g.getConsList(c))
        rateB = rateB * (ratePeriod / g.getPhaseCount(dest))
        if dest==a :
            tmp = rateB
            rateB = rateA
            rateA = tmp
        if rateA == 0 or rateB == 0 :
            fractions = {}
            print ("rateA == 0 || rateB == 0")
            return False
        

        ratioAB = Fraction(rateA, rateB);
        fractionB = fractionA * ratioAB;

        knownFractionB = fractions[b];

        if (knownFractionB != Fraction(0,1) and fractionB != knownFractionB)  :
            fractions = {}
            return False
        
        elif (knownFractionB == Fraction(0,1)) :

    
            fractions[b] = fractionB
            calcFractionsConnectedActors(g, fractions, b, ratePeriod)
            if (fractions[b] == Fraction(0,1)) :
                return False
            
    return True



def calcRepetitionVector(g,fractions,ratePeriod) :

    repetitionVector = {}
    l = 1
    
    for v in g.getTaskList() :
        l = lcm(l,fractions[v].denominator)
        
    if (l == 0) :
        print("Zero vector ?")
        raise ValueError

    for v in g.getTaskList() :
        repetitionVector[v] = (fractions[v].numerator * l) /  fractions[v].denominator

    legcd = repetitionVector[g.getTaskList()[0]];

    for v in g.getTaskList() :
        legcd = gcd(legcd, repetitionVector[v])


    if (legcd <= 0) : raise ValueError 

    for v in g.getTaskList() :
        repetitionVector[v] = repetitionVector[v] / legcd


    for v in g.getTaskList() :
        repetitionVector[v] = repetitionVector[v] * ratePeriod

    return repetitionVector


def checkRepetitionVector(g) :

    fractions = {};
    for v in g.getTaskList() :
        fractions[v] = Fraction(0,1)

    ratePeriod = 1;

    for c in g.getArcList() :
        ratePeriod = lcm(ratePeriod,g.getPhaseCount(g.getSource(c)));
        ratePeriod = lcm(ratePeriod,g.getPhaseCount(g.getTarget(c)));

    if (ratePeriod <= 0) :
        raise ValueError


    for v in g.getTaskList() :
        if (fractions[v] == Fraction(0,1)) :
            fractions[v] = Fraction(1,1)
            if (not calcFractionsConnectedActors(g, fractions, v, ratePeriod)) :
                return False


    repetitionVector =  calcRepetitionVector(g,fractions, ratePeriod);

    legcd = repetitionVector[g.getTaskList()[0]] / g.getPhaseCount(g.getTaskList()[0])

    for v in g.getTaskList() :
        legcd = gcd(legcd, repetitionVector[v] / g.getPhaseCount(v))

    for v in g.getTaskList() :
        print"%s \t: %d\tx %d \t = %d VS %d" % (g.getTaskName(v),repetitionVector[v] / g.getPhaseCount(v),g.getPhaseCount(v), repetitionVector[v],g.getRepetitionFactor(v)),
        if (g.getRepetitionFactor(v) ) != repetitionVector[v] / (g.getPhaseCount(v) * legcd) :
            print "error"   
            #raise Error()
        else :
            print ""

    return True

def computeRepetitionVector(g) :

    fractions = {};
    for v in g.getTaskList() :
        fractions[v] = Fraction(0,1)

    ratePeriod = 1;

    for c in g.getArcList() :
        ratePeriod = lcm(ratePeriod,g.getPhaseCount(g.getSource(c)));
        ratePeriod = lcm(ratePeriod,g.getPhaseCount(g.getTarget(c)));

    if (ratePeriod <= 0) :
        raise ValueError


    for v in g.getTaskList() :
        if (fractions[v] == Fraction(0,1)) :
            fractions[v] = Fraction(1,1)
            if (not calcFractionsConnectedActors(g, fractions, v, ratePeriod)) :
                return False


    repetitionVector =  calcRepetitionVector(g,fractions, ratePeriod);

    legcd = repetitionVector[g.getTaskList()[0]] / g.getPhaseCount(g.getTaskList()[0])

    for v in g.getTaskList() :
        legcd = gcd(legcd, repetitionVector[v] / g.getPhaseCount(v))


    for v in g.getTaskList() :
        g.setRepetitionFactor(v,repetitionVector[v] / (g.getPhaseCount(v) * legcd))

    return True


if __name__ == "__main__":

    newgraph = generate("autogen")
    checkRepetitionVector(newgraph)
    print "AutoCheck Done"



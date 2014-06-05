from models.lcm import lcmList
import logging


class Normalized :
    """This class is used to normalized and unnormalized a graph.
    When un-normalized, if the graph were not normalized by the same object, 
    a coefficient vector is asked (same size as the number of arcs/edges).
    """

    def __init__(self, graph):
        """Initialize the object.
        """
        self.graph = graph
        self.coefVector = None
        self.log = logging.getLogger('normalization')

    def getGraphUnNorm(self, graph, coefVector = None):
        """Un-normalize according to a coefficient vector.
        
        Return
        ------
        Return the unormalize graph.
        """
        if not graph.isNormalized():
            return graph
        
        if coefVector == None:
            if self.coefVector == None :
                self.log.error("You must specified a coefficient vector for denormalize !")
                return
            coefVector = self.coefVector
        else:
            if self.__testCoefVector(coefVector) == False:
                self.log.error("Coefficient vector specified is not valid !")
                return

        for arc in self.graph.getArcList():
            coef = coefVector[arc]
            self.graph.setProdList(arc,[int(x/coef) for x in self.graph.getProdList(arc)])
            self.graph.setConsList(arc,[int(x/coef) for x in self.graph.getConsList(arc)])

            self.graph.setInitialMarking(arc,int(self.graph.getInitialMarking(arc)/coef))

            if self.graph.isInitialized() :
                self.graph.setProdInitList(arc, [int(x/coef) for x in self.graph.getProdInitList(arc)])
                self.graph.setConsInitList(arc, [int(x/coef) for x in self.graph.getConsInitList(arc)])
            
            if self.graph.isThresholded() :
                self.graph.setConsThresholdList(arc, [int(x/coef) for x in self.graph.getConsThresholdList(arc)])

            if self.graph.isThresholded() and self.graph.isInitialized() :
                self.graph.setConsInitThresholdList(arc, [int(x/coef) for x in self.graph.getConsInitThresholdList(arc)])
        return self.graph
    
    def __testCoefVector(self, coefVector):
        if len(coefVector) != len(self.graph.getArcList()):
            return False
        
        for arc in self.graph.getArcList():
            coef = coefVector[arc]
            if self.__testCoef(coef, self.graph.getProdList(arc)) == False:
                return False
            if self.__testCoef(coef, self.graph.getConsList(arc)) == False:
                return False
            if self.__testCoef(coef, [self.graph.getInitialMarking(arc)]) == False:
                return False

            if self.graph.isInitialized() :
                if self.__testCoef(coef, self.graph.getProdInitList(arc)) == False:
                    return False
                if self.__testCoef(coef, self.graph.getConsInitList(arc)) == False:
                    return False
            
            if self.graph.isThresholded() :
                if self.__testCoef(coef, self.graph.getConsThresholdList(arc)) == False:
                    return False

            if self.graph.isThresholded() and self.graph.isInitialized() :
                if self.__testCoef(coef, self.graph.getConsInitThresholdList(arc)) == False:
                    return False
            return True

    def __testCoef(self, coef, coefList):
        for x in coefList:
            if (float(x)/float(coef)) != (x/coef):
                return False
        return True 

        
        
        
    def getGraphNorm(self):
        """Normalize according to a coefficient vector.
        
        Return
        ------
        Return the un-normalize graph.
        """
        if self.graph.isNormalized():
            return self.graph

        self.getVectorNorm()

        for arc in self.graph.getArcList():
            coef = self.coefVector[arc]
            
            self.graph.setProdList(arc,[int(x*coef) for x in self.graph.getProdList(arc)])
            self.graph.setConsList(arc,[int(x*coef) for x in self.graph.getConsList(arc)])

            self.graph.setInitialMarking(arc,int(self.graph.getInitialMarking(arc)*coef))

            if self.graph.isInitialized() :
                self.graph.setProdInitList(arc, [int(x*coef) for x in self.graph.getProdInitList(arc)])
                self.graph.setConsInitList(arc, [int(x*coef) for x in self.graph.getConsInitList(arc)])
            
            if self.graph.isThresholded() :
                self.graph.setConsThresholdList(arc, [int(x*coef) for x in self.graph.getConsThresholdList(arc)])

            if self.graph.isThresholded() and self.graph.isInitialized() :
                self.graph.setConsInitThresholdList(arc, [int(x*coef) for x in self.graph.getConsInitThresholdList(arc)])

        return self.graph

    def getvectorUnNorm(self):
        """Compute the smallest vector for denormalized the graph.
        
        ------
        Return the the vector of coefficient for denormalize the graph.
        """
        if not self.graph.isNormalized():
            return

        coef = {}
        for arc in self.graph.getArcList():
            coef[arc] = self.graph.getGcd(arc)
        self.coefVector = coef
        return self.coefVector

    def getVectorNorm(self):
        """Compute the normalization vector of an un-normalize graph.
        
        Return
        ------
        Return the the vector of coefficient for normalize the graph.
        """
        coef = {}
        lcmV = 1
        for arc in self.graph.getArcList():
            rate = self.graph.getRepetitionFactor(self.graph.getSource(arc)) * sum(self.graph.getProdList(arc))
            lcmV = lcmList([lcmV, rate])
            
        for arc in self.graph.getArcList():
            Ri = self.graph.getRepetitionFactor(self.graph.getSource(arc))
            Zi = sum(self.graph.getProdList(arc))
            coef[arc] = (lcmV/Ri)/Zi
        self.coefVector = coef
        return self.coefVector

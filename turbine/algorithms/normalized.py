from models.lcm import lcmList
import copy


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

    def getGraphUnNorm(self, graph, coefVector):
        """Un-normalize according to a coefficient vector.
        
        Return
        ------
        Return the unormalize graph.
        """
        if not graph.isNormalized():
            return graph
        
        un_graph = copy.deepcopy(graph)
        for arc in self.graph.getArcList():
            coef = coefVector[arc]
            un_graph.setProdList(arc,[int(x/coef) for x in un_graph.getProdList(arc)])
            un_graph.setConsList(arc,[int(x/coef) for x in un_graph.getConsList(arc)])

            un_graph.setInitialMarking(arc,int(un_graph.getInitialMarking(arc)/coef))

            if un_graph.isInitialized() :
                un_graph.setProdInitList(arc, [int(x/coef) for x in un_graph.getProdInitList(arc)])
                un_graph.setConsInitList(arc, [int(x/coef) for x in un_graph.getConsInitList(arc)])
            
            if un_graph.isThresholded() :
                un_graph.setConsThresholdList(arc, [int(x/coef) for x in un_graph.getConsThresholdList(arc)])

            if un_graph.isThresholded() and un_graph.isInitialized() :
                un_graph.setConsInitThresholdList(arc, [int(x/coef) for x in un_graph.getConsInitThresholdList(arc)])
        un_graph.setName(un_graph.getName()+"_unnorm")
        return un_graph
        
        
    def getGraphNorm(self):
        """Normalize according to a coefficient vector.
        
        Return
        ------
        Return the un-normalize graph.
        """
        if self.graph.isNormalized():
            return self.graph
        
        n_graph = copy.deepcopy(self.graph)
        n_graph.setName(n_graph.getName()+"_norm")

        self.getVectorNorm()
        
        for arc in self.graph.getArcList():
            coef = self.coefVector[arc]
            
            n_graph.setProdList(arc,[int(x*coef) for x in n_graph.getProdList(arc)])
            n_graph.setConsList(arc,[int(x*coef) for x in n_graph.getConsList(arc)])

            n_graph.setInitialMarking(arc,int(n_graph.getInitialMarking(arc)*coef))

            if n_graph.isInitialized() :
                n_graph.setProdInitList(arc, [int(x*coef) for x in n_graph.getProdInitList(arc)])
                n_graph.setConsInitList(arc, [int(x*coef) for x in n_graph.getConsInitList(arc)])
            
            if n_graph.isThresholded() :
                n_graph.setConsThresholdList(arc, [int(x*coef) for x in n_graph.getConsThresholdList(arc)])

            if n_graph.isThresholded() and n_graph.isInitialized() :
                n_graph.setConsInitThresholdList(arc, [int(x*coef) for x in n_graph.getConsInitThresholdList(arc)])

        return n_graph
    
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

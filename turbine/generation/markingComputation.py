import logging

from algorithms.solve_SC1 import SolverSC1
from algorithms.solve_SC2 import SolverSC2


def __sumPreload(graph):
    tot = 0
    for edge in graph.getArcList() :
        tot += graph.getInitialMarking(edge)
    return tot

def __clearInitialMarking(graph):
    for edge in graph.getArcList() :
        graph.setInitialMarking(edge, 0)


########################################################################
#                           generate preload                           #
########################################################################
def generateInitialMarking(graph, solver="auto", GLPKVerbose=False, LPFileName=None):
    """Step 3
    """
    __clearInitialMarking(graph)

    if solver == "SC2" :
        solver = SolverSC2(graph, GLPKVerbose, LPFileName)
    elif solver == "SC1" :
        solver = SolverSC1(graph, GLPKVerbose, LPFileName)
    elif solver == "auto" :
        if __SC2RowCount(graph) < __SC1RowCount(graph) :
            solver = SolverSC2(graph, GLPKVerbose, LPFileName)
            logging.info("choose solver SC2")
        else:
            solver = SolverSC1(graph, GLPKVerbose, LPFileName)
            logging.info("choose solver SC1")
    else :
        logging.error("solver : wrong argument")
        return

    solver.generateInitialMarking()
    M0tot = __calcReEntrant(graph)
    logging.info("Mem tot (reentrant) : " + str(M0tot))
    

def __SC2RowCount(graph):
    FRowCount = graph.getArcCount()
    rowCount = 0
    for task in graph.getTaskList():
        taskReEntrant = 0
        for arc in graph.getInputArcList(task):
            if graph.isArcReEntrant(arc) :
                taskReEntrant += 1
        FRowCount -= taskReEntrant
        rowCount += ((graph.getInputDegree(task) - taskReEntrant) * (graph.getOutputDegree(task) - taskReEntrant))
    return rowCount + FRowCount

def __SC1RowCount(graph):
    rowCount = 0
    for arc in graph.getArcList():
        source = graph.getSource(arc)
        target = graph.getTarget(arc)
        if not graph.isArcReEntrant(arc) :
            if graph.isInitialized() :
                sourcePhaseCount = graph.getPhaseCount(source) + graph.getPhaseCountInit(source)
                targetPhaseCount = graph.getPhaseCount(target) + graph.getPhaseCountInit(target)
                rowCount += sourcePhaseCount * targetPhaseCount
            else :
                rowCount += graph.getPhaseCount(source) * graph.getPhaseCount(target)
    return rowCount

def __calcReEntrantPreload(graph):
    M0tot = 0
    for arc in graph.getArcList() :
        if graph.isArcReEntrant(arc) :
            cons = graph.getConsList(arc)
            if graph.isInitialized():
                cons += graph.getConsInitList(arc)

            step = graph.getGcd(arc)
            M0 = sum(cons) - step
            
            if M0 % step != 0 or M0 == 0:
                M0 += (step - M0 % step)

            graph.setInitialMarking(arc, M0)
            M0tot += M0
            logging.debug("Reentrant initial marking for arc : " + str(arc) + " : " + str(M0))
    return M0tot

def __calcReEntrant(graph):
    M0tot = 0
    for arc in graph.getArcList() :
        if graph.isArcReEntrant(arc) :
            phaseCount = graph.getPhaseCount(graph.getTarget(arc))
            prodList = graph.getProdList(arc)
            consList = graph.getConsList(arc)
            thresholdList = graph.getConsThresholdList(arc)
            if graph.isInitialized() :
                phaseCount += graph.getPhaseCountInit(graph.getTarget(arc))
                prodList = graph.getProdInitList(arc) + prodList
                consList = graph.getConsInitList(arc) + consList
                thresholdList = graph.getConsInitThresholdList(arc) + thresholdList
        
            retMax = graph.getConsList(arc)[0]
        
            predOut = 0
            predIn = 0
            In = 0
            for phase in xrange(phaseCount):
                if phase > 0 :
                    predOut += prodList[phase - 1]
                    predIn += consList[phase - 1]
                In += consList[phase]
        
                W2 = In - predOut
                if graph.isThresholded() :
                    W2 += predIn + thresholdList[phase] - In
        
                if retMax < W2 : retMax = W2
                graph.setInitialMarking(arc, retMax)
                M0tot += retMax
                logging.debug("Reentrant initial marking for arc : " + str(arc) + " : " + str(retMax))

    return M0tot


# def __generateNewDFToolsPreload(graph):
#     #Pour chaque noeud du graphe
#     #   Pour chaque arc entrant dans la meme composante connexe
#     #        Q = taux de production * Vecteur de repetition
#     #   On retire le noeud
#     #~ print "Begin generateDFToolsPreload -"
#     for dst in graph.getTaskList() :
#         SCC = strongly_connected_components_with_empty(graph,dst)
#         for src in SCC :
#             for edge in graph.getArcList(source=src,target=dst) : 
#                 N = graph.getRepetitionFactor(src) * sum(graph.getProdList(edge))
#                 graph.setInitialMarking(edge,N)
#                 #print  "  Add preload %d" % N
#     return
# 
# 
# def __generateDFToolsPreload(graph):
#     #Pour chaque noeud du graphe
#     #   Pour chaque arc entrant dans la meme composante connexe
#     #        Q = taux de production * Vecteur de repetition
#     #   On retire le noeud
#     #~ print "Begin generateDFToolsPreload -"
#     for dst in graph.getTaskList() :
#         SCC = tarjan_empty_recursive(graph,dst)
#         for src in SCC :
#             for edge in graph.getArcList(source=src,target=dst) : 
#                 N = graph.getRepetitionFactor(src) * graph.getProdList(edge)[0]
#                 graph.setInitialMarking(edge,N)
#                 #print  "  Add preload %d" % N
#     return
# 
# 
# def __generateSDF3Preload(graph):
# 
#     # step 1 - recheche d'un cycle de depart
#     arc = getArcInEmptyCycle(graph) 
#     while arc != None : # step 2 - tant qu'il y a un cycle
#         a = graph.getSource(arc)
#         b = graph.getTarget(arc)
#         #print "un cycle de plus avec %d jetons" %  __sumPreload(graph)
#         for edge in graph.getArcList(source=a,target=b) :  # Pour l'ensemble des canaux entre a et b
#             
#             # On ajoute N jetons dans ce canal avec 
#             # N = RV[a] * le taux de production dans l'arc
#             # plutot que de supprimer l'arc comme prevu, on ignorera les arc avec jeton
# 
#             N = graph.getRepetitionFactor(a) * graph.getProdList(edge)[0]
#             graph.setInitialMarking(edge,N)
#         arc = getArcInEmptyCycle(graph) 
# 
#     # Step 3 - on termine sur une execution symbolique pour melanger les jeton
#     # TODO - Pas fait !
#         
#     
# def __generateNewSDF3Preload(realgraph):
#     fakegraph = copy.deepcopy(realgraph)
# 
#     # step 1 - recheche d'un cycle de depart
#     arc = getArcInCycle(fakegraph) 
#     while arc != None : # step 2 - tant qu'il y a un cycle
#         a = fakegraph.getSource(arc)
#         b = fakegraph.getTarget(arc)
#         #print "un cycle de plus avec %d jetons" %  __sumPreload(realgraph)
#         for edge in list(fakegraph.getArcList(source=a,target=b)) :  # Pour l'ensemble des canaux entre a et b
#             
#             # On ajoute N jetons dans ce canal avec 
#             # N = RV[a] * le taux de production dans l'arc
#             # plutot que de supprimer l'arc comme prevu, on ignorera les arc avec jeton
# 
#             N = realgraph.getRepetitionFactor(a) * sum(realgraph.getProdList(edge))
#             realgraph.setInitialMarking(edge,N)
#             fakegraph.removeArc(edge)
#         arc = getArcInCycle(fakegraph) 
# 
#     # Step 3 - on termine sur une execution symbolique pour melanger les jeton
#     # TODO - Pas fait !
#         

from models.graph import Graph
import networkx as nx


def isHided(G, V) :
    for VW in G.getArcList(target=V) :
        if  G.getInitialMarking(VW) != 0 :
            return True
    return False



def strongly_connected_components_with_empty(G, star):
    """ Same version from network X with some changes 
    """
    preorder = {}
    lowlink = {}    
    scc_found = {}
    scc_queue = []

    i = 0  # Preorder counter
    for source in G.getTaskList():
        if source not in scc_found:
            queue = [source]
            while queue:
                v = queue[-1]
                if v not in preorder:
                    i = i + 1
                    preorder[v] = i
                done = 1
                v_nbrs = [w for (_, w, _) in G.getArcList(source=v) if not isHided(G, w)]
                for w in v_nbrs:
                    if w not in preorder:
                        queue.append(w)
                        done = 0
                        break
                if done == 1:
                    lowlink[v] = preorder[v]
                    for w in v_nbrs:
                        if w not in scc_found:
                            if preorder[w] > preorder[v]:
                                lowlink[v] = min([lowlink[v], lowlink[w]])
                            else:
                                lowlink[v] = min([lowlink[v], preorder[w]])
                    queue.pop()
                    if lowlink[v] == preorder[v]:
                        scc_found[v] = True
                        scc = [v]
                        while scc_queue and preorder[scc_queue[-1]] > preorder[v]:
                            k = scc_queue.pop()
                            scc_found[k] = True
                            scc.append(k)
                        if star in scc :
                            return scc
                    else:
                        scc_queue.append(v)
    raise Error()
    return None



def tarjan_recursive(g):
        S = []
        S_set = set()
        index = {}
        lowlink = {}
        ret = []

        def visit(v):
                index[v] = len(index)
                lowlink[v] = index[v]
                S.append(v)
                S_set.add(v)
                for vw in g.getArcList(source=v) :
                    if g.getSource(vw) != v :
                        raise SuperBug()
                    w = g.getTarget(vw)
                    if w not in index:
                                visit(w)
                                lowlink[v] = min(lowlink[w], lowlink[v])
                    elif w in S_set:
                                lowlink[v] = min(lowlink[v], index[w])
                if lowlink[v] == index[v]:
                        scc = []
                        w = None
                        while v != w:
                                w = S.pop()
                                scc.append(w)
                                S_set.remove(w)
                        ret.append(scc)

        for v in g.getTaskList():
                if not v in index:
                        visit(v)
        return ret


def tarjan_empty_recursive(g, star):
        S = []
        S_set = set()
        index = {}
        lowlink = {}

        def visit(v):
                index[v] = len(index)
                lowlink[v] = index[v]
                S.append(v)
                S_set.add(v)
                for vw in g.getArcList(source=v) :
                    if g.getSource(vw) != v :
                        raise SuperBug()
                    w = g.getTarget(vw)
		    if isHided(g, w) :
			    continue 
                    if w not in index:
				scc = visit(w)
				if scc != [] : return scc
                                lowlink[v] = min(lowlink[w], lowlink[v])
                    elif w in S_set:
                                lowlink[v] = min(lowlink[v], index[w])
                if lowlink[v] == index[v]:
                        scc = []
                        w = None
                        while v != w:
                                w = S.pop()
                                scc.append(w)
                                S_set.remove(w)
			if star in scc :
				return scc
		return []

        scc = visit(star)
        if  scc != [] : 
            return scc
	raise Error()
        return None


def tarjan(G) :
 # index := 0
 # S := empty
 # for each v in V do
 #   if (v.index is undefined) then
 #     strongconnect(v)
 #   end if
 # end for
    global tarjan_mindex, tarjan_index, tarjan_lowlink, tarjan_S 
    tarjan_mindex = 0
    tarjan_index = {}
    tarjan_lowlink = {}
    tarjan_S = []
    SCC = []
    for V in G.getTaskList() :
        if V not in tarjan_index :
          SCC = SCC + (strongconnect(G, V))
    return SCC



def strongconnect(G, V) :
    global tarjan_mindex, tarjan_index, tarjan_lowlink, tarjan_S 

    tarjan_index[V] = tarjan_mindex
    tarjan_lowlink[V] = tarjan_mindex
    tarjan_mindex = tarjan_mindex + 1
    tarjan_S.append(V)
    SCC = []
    for VW in G.getArcList(source=V) :
        V = G.getSource(VW)
        W = G.getTarget(VW)
        if W not in tarjan_index :
            SCC = SCC + strongconnect(G, W)
            tarjan_lowlink[V] = min(tarjan_lowlink[V] , tarjan_lowlink[W])
        else :
            if W in tarjan_S :
                tarjan_lowlink[V] = min(tarjan_lowlink[V] , tarjan_index[W])
    if tarjan_lowlink[V] == tarjan_index[V] :
        NSCC = []
        while True:
            W = tarjan_S.pop()
            NSCC.append(W)
            if W == V:
                break
        SCC = SCC + [NSCC]
    return SCC

def isHided(G, V) :
    for VW in G.getArcList(target=V) :
        if  G.getInitialMarking(VW) != 0 :
            return True
    return False

def tarjanEmpty(G) :
    global tarjan_mindex, tarjan_index, tarjan_lowlink, tarjan_S 
    tarjan_mindex = 0
    tarjan_index = {}
    tarjan_lowlink = {}
    tarjan_S = []
    SCC = []
    for V in G.getTaskList() :
      if isHided(G, V) :
          continue
      if V not in tarjan_index :
          SCC = SCC + (strongconnectEmpty(G, V))
    return SCC



def strongconnectEmpty(G, V) :
    global tarjan_mindex, tarjan_index, tarjan_lowlink, tarjan_S 
    ####print  "strongconnect(G ," + str(V) + " ,"  + " ," + str(tarjan_index) + " ," + str(tarjan_lowlink) + ") "

    tarjan_index[V] = tarjan_mindex
    tarjan_lowlink[V] = tarjan_mindex
    tarjan_mindex = tarjan_mindex + 1
    tarjan_S.append(V)
    SCC = []
    for VW in G.getArcList(source=V) :
        V = G.getSource(VW)
        W = G.getTarget(VW)
        if isHided(G, W) :
          continue
        if W not in tarjan_index :
            SCC = SCC + strongconnectEmpty(G, W)
            tarjan_lowlink[V] = min(tarjan_lowlink[V] , tarjan_lowlink[W])
        else :
            if W in tarjan_S :
                tarjan_lowlink[V] = min(tarjan_lowlink[V] , tarjan_index[W])
    if tarjan_lowlink[V] == tarjan_index[V] :
        NSCC = []
        while True:
            W = tarjan_S.pop()
            NSCC.append(W)
            if W == V:
                break
        # ##print NSCC
        SCC = SCC + [NSCC]
    return SCC

from random import *

from models.gcd import *
from models.lcm import *


def isContainsCycle(graph):

    visited = set()

    for task in graph.getTaskList() :
        if task not in visited :
            # print "begin new task %s" % (task)
            stack = [task]
            path = []
            while stack != []:
                v = stack.pop()
                # print "pop %s%s" % (v,npath)
                path = path[:]
                if v not in path:
                    path.append(v)
                    visited.add(v)
                else :                    
                    # print "already visit %s" % (v)
                    dfs_result(v, path)
                    return True
                for vw in graph.getArcList(source=v):
                    w = graph.getTarget(vw)
                    if w not in path:
                        # print "push %s%s" % (w,path)
                        stack.append(w)
                    else :
                        # print "already visit %s" % (w)
                        dfs_result(w, path)
                        return True

    return False

# use by SDF3 algorithm !
def getArcInCycle(graph):

    visited = set()
  
    for task in graph.getTaskList() :
        if task not in visited :
            # print "begin new task %s" % (task)
            stack = [(task, set())]
            cvisited = set()
            while stack != []:
                (v, npath) = stack.pop()
                # print "pop %s%s" % (v,npath)
                cvisited = npath
                if v not in cvisited:
                    cvisited.add(v)
                    visited.add(v)
                else :                    
                    # print "already visit %s" % (v)
                    raise ValueError
                    # return graph.getArcList(source = v, target = v)[0]
                for vw in graph.getArcList(source=v):
                    w = graph.getTarget(vw) 
                    if w not in cvisited:
                        # print "push %s%s" % (w,path)
                        stack.append((w, cvisited.copy()))
                    else :
                        # print "already visit %s" % (w)
                        return vw

    return None

def getArcInEmptyCycle(graph):

    visited = set()
  
    for task in graph.getTaskList() :
        if task not in visited :
            # print "begin new task %s" % (task)
            stack = [(task, [])]
            path = []
            while stack != []:
                (v, npath) = stack.pop()
                # print "pop %s%s" % (v,npath)
                path = npath[:]
                if v not in path:
                    path.append(v)
                    visited.add(v)
                else :                    
                    # print "already visit %s" % (v)
                    raise ValueError
                    # return graph.getArcList(source = v, target = v)[0]
                for vw in graph.getArcList(source=v):
                    if graph.getInitialMarking(vw) != 0 : 
                        continue
                    w = graph.getTarget(vw) 
                    if w not in path:
                        # print "push %s%s" % (w,path)
                        stack.append((w, path[:]))
                    else :
                        # print "already visit %s" % (w)
                        return vw

    return None

    

def getCycle(graph, nodeSkipCondition=(lambda x, y : False) , arcSkipCondition=(lambda x, y : False)):

    visited = []
    res = []
    def dfs_result(last, path) :
        # print "return " + str(path) + " with last " + str(last)
        before = last
        for node in reversed(path) :
            if node == last :
                arcs = graph.getArcList(source=node, target=before)
                if len(arcs) == 0 :
                    raise ValueError
                res.append(arcs[0])
                return
            else :
                arcs = graph.getArcList(source=node, target=before)
                if len(arcs) == 0 :
                    raise ValueError
                res.append(arcs[0])
                before = node
        raise ValueError

  
    for task in graph.getTaskList() :
        if nodeSkipCondition(graph, task) : 
            continue
        if task not in visited :
            # print "begin new task %s" % (task)
            stack = [(task, [])]
            path = []
            while stack != []:
                (v, npath) = stack.pop()
                # print "pop %s%s" % (v,npath)
                path = npath[:]
                if v not in path:
                    path.append(v)
                    visited.append(v)
                else :                    
                    # print "already visit %s" % (v)
                    dfs_result(v, path)
                    return res
                for vw in graph.getArcList(source=v):
                    if arcSkipCondition(graph, vw) : 
                        continue
                    w = graph.getTarget(vw)
                    if nodeSkipCondition(graph, vw) : 
                        continue   
                    if w not in path:
                        # print "push %s%s" % (w,path)
                        stack.append((w, path[:]))
                    else :
                        # print "already visit %s" % (w)
                        dfs_result(w, path)
                        return res

    return None



def findEmptyCycle(graph) :
    return getCycle(graph, arcSkipCondition=(lambda g, a : g.getInitialMarking(a) != 0))

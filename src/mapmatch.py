import sumolib
import itertools
import numpy as np
#import os
#import sys
from itertools import groupby
#import xml
import skmob
#from xml.dom import minidom
import copy
#import subprocess
from math import sqrt, sin, cos, pi, asin
from skmob.tessellation import tilers
import collections
import pandas as pd
from scipy.spatial.distance import cdist
import heapq
from itertools import chain



def getOptimalPath(self, fromEdge, toEdge, fastest=False, maxCost=1e400, vClass=None, reversalPenalty=0,
                       includeFromToCost=True, withInternal=False, ignoreDirection=False,
                       fromPos=0, toPos=0):
        """
        Finds the optimal (shortest or fastest) path for vClass from fromEdge to toEdge
        by using using Dijkstra's algorithm.
        It returns a pair of a tuple of edges and the cost.
        If no path is found the first element is None.
        The cost for the returned path is equal to the sum of all edge costs in the path,
        including the internal connectors, if they are present in the network.
        The path itself does not include internal edges except for the case
        when the start or end edge are internal edges.
        The search may be limited using the given threshold.
        """

        def speedFunc(edge):
            return edge.getSpeed() if fastest else 1.0

        if self.hasInternal:
            appendix = ()
            appendixCost = 0.
            while toEdge.getFunction() == "internal":
                appendix = (toEdge,) + appendix
                appendixCost += toEdge.getLength() / speedFunc(toEdge)
                toEdge = list(toEdge.getIncoming().keys())[0]
        fromCost = fromEdge.getLength() / speedFunc(fromEdge) if includeFromToCost else 0
        q = [(fromCost, fromEdge.getID(), (fromEdge, ), ())]
        if fromEdge == toEdge and fromPos > toPos and not ignoreDirection:
            # start search on successors of fromEdge
            q = []
            startCost = (fromEdge.getLength() - fromPos) / speedFunc(fromEdge) if includeFromToCost else 0
            for e2, conn in fromEdge.getAllowedOutgoing(vClass).items():
                q.append((startCost + e2.getLength() / speedFunc(e2), e2.getID(), (fromEdge, e2), ()))

        seen = set()
        dist = {fromEdge: fromEdge.getLength() / speedFunc(fromEdge)}
        while q:
            cost, _, e1via, path = heapq.heappop(q)
            e1 = e1via[-1]
            if e1 in seen:
                continue
            seen.add(e1)
            path += e1via
            if e1 == toEdge:
                if self.hasInternal:
                    return path + appendix, cost + appendixCost
                if includeFromToCost and toPos == 0:
                    # assume toPos=0 is the default value
                    return path, cost
                return path, cost + (-toEdge.getLength() + toPos) / speedFunc(toEdge)
            if cost > maxCost:
                return None, cost

            for e2, conn in chain(e1.getAllowedOutgoing(vClass).items(),
                                  e1.getIncoming().items() if ignoreDirection else []):
                # print(cost, e1.getID(), e2.getID(), e2 in seen)
                if e2 not in seen:
                    newCost = cost + e2.getLength() / speedFunc(e2)
                    if e2 == e1.getBidi():
                        newCost += reversalPenalty
                    minPath = (e2,)
                    if self.hasInternal:
                        viaPath, minInternalCost = self.getInternalPath(conn, fastest=fastest)
                        if viaPath is not None:
                            newCost += minInternalCost
                            if withInternal:
                                minPath = tuple(viaPath + [e2])
                    if e2 not in dist or newCost < dist[e2]:
                        dist[e2] = newCost
                        heapq.heappush(q, (newCost, e2.getID(), minPath, path))
        return None, 1e400


 # add dynamically the getOptimalPath function
    
setattr(sumolib.net.Net, 'getOptimalPath', getOptimalPath)


def sumo_map_matching(points, road_network, road_network_path, road_network_int, 
                      edge_from, edge_to, accept_th=5e-5, early_stop=True):
    
    
   
  
    edge_list_best, best_sspd, length_best, best_conf = None, 10**5, None, None
       
        
    # 1 FASTEST PATH
    
    fast_edge_list, sspd_fast, dist, alg = match_with_fastest(points, road_network, road_network_int, edge_from, edge_to)
    
    if sspd_fast <= accept_th:
        return fast_edge_list, sspd_fast, dist, alg
    
    if sspd_fast < best_sspd:
        edge_list_best = fast_edge_list
        best_sspd = sspd_fast
        length_best = dist
        best_conf = alg
    
    
    # 2 SHORTEST PATH
    
    short_edge_list, sspd_short, dist, alg = match_with_shortest(points, road_network, road_network_int, edge_from, edge_to)
    
    if sspd_short <= accept_th:
        return short_edge_list, sspd_short, dist, alg
    
    if sspd_short < best_sspd:
        edge_list_best = short_edge_list
        best_sspd = sspd_short
        length_best = dist
        best_conf = alg
    
    # 3 AUTOADAPTING MAP MATCHING 
    
    aa_edge_list, sspd_aa, dist, alg = autoadapting_map_matching(points, road_network, 
                                                            road_network_int, edge_from, edge_to, fastest=True,
                                                              accept_th=5e-5, early_stop=True)
    if sspd_aa < best_sspd:
    
        return aa_edge_list, sspd_aa, dist, alg
    
    
    return edge_list_best, best_sspd, length_best, best_conf
    
    
    
def autoadapting_map_matching(points, road_network, road_network_int, edge_from, edge_to, fastest=True,
                              accept_th=5e-5, early_stop=True):

    
    edge_list_best, best_sspd, length_best, best_dist, best_th = None, 10**5, None, None, None
    
    # search parameters
    max_dist_list = [0, 0.01, 0.025, 0.05, 0.1]#, 0.2, 1, 2]
    th_list = [1]#, 2]
    
    #print("map_matching_alg New autoadapting_map_matching su LISTE")

    for th in th_list:
        
        '''try:
            edges_map_matched = map_matching_alg(points, road_network, edge_from, edge_to, max_dist_list, 
                                                 th=th, fastest=fastest)
        except:
            print("error")'''
        
        edges_map_matched = map_matching_alg(points, road_network, edge_from, edge_to, max_dist_list, 
                                                 th=th, fastest=fastest)
        
        # compute scores
        
        for ind, e_list in enumerate(edges_map_matched):
            
            #compute traj
            tdf_traj = tdf_from_edgelist(e_list, road_network)
            points_traj = tdf_traj[['lng','lat']].values
            
            #compute sspd
            sspd = e_sspd(points_traj, np.array(points))
            #print(sspd)
            
            if early_stop and sspd<=accept_th:
                
                #print("early stop with "+str(sspd<accept_th))
                
                edge_list_best = e_list
                best_sspd = sspd
                length_best = sumolib.route.getLength(road_network_int, e_list)
                best_dist = max_dist_list[ind]
                best_th = th
                
                return edge_list_best, best_sspd, length_best, (best_dist, best_th)
            
            
            elif sspd<best_sspd:
                
                #print("UPDate")
                
                edge_list_best = e_list
                best_sspd = sspd
                length_best = sumolib.route.getLength(road_network_int, e_list)
                best_dist = max_dist_list[ind]
                best_th = th
                
    
    return edge_list_best, best_sspd, length_best, (best_dist, best_th)



def map_matching_alg(points, road_network, edge_from, edge_to, max_dist_list, th=1, fastest=True):

    # NEW STEP 1 
    #print("New algorithm LISTA th="+str(th))
    edge_list, edge_dist_list, list_edge_list, edges_no_loops = [], [], [], []

    for p in points:
        edge, dist = get_closest_edge_from_point(road_network, p[1], p[0], return_dist=True)
        edge_list.append(edge)
        edge_dist_list.append(dist)

    edge_list_th = keep_th_consecutive(edge_list, th=th)
    
    for max_dist in max_dist_list:
    
        edges_new_way = []

        for r_id in edge_list_th:
            indices = [i for i in range(len(edge_list)) if edge_list[i] == r_id]
            for i in indices:
                if edge_dist_list[i]<=max_dist:
                    edges_new_way.append(r_id)
                    break;


        if len(edges_new_way)>2:
            if edges_new_way[0] != edge_from:
                        edges_new_way = [edge_from]+edges_new_way
            if edges_new_way[-1] != edge_to:
                        edges_new_way = edges_new_way+[edge_to]
        else:
            edges_new_way = [edge_from, edge_to]

        list_edge_list.append(edges_new_way)

    edges_duarouter = my_get_edges_from_duarouter(list_edge_list, road_network, fastest=fastest);

    for e_list in edges_duarouter:
        edges_no_loops.append(remove_loops_edge_list(e_list));

    return edges_no_loops


def my_get_edges_from_duarouter(list_edge_list, road_network, fastest=True):
    

    duarouter_edges = []

    for edge_list in list_edge_list:
    
        edges_reconstructed = []

        for i in range(len(edge_list)-1):

            e0 = road_network.getEdge(edge_list[i])
            e1 = road_network.getEdge(edge_list[i+1])

            path_e0_e1 = road_network.getOptimalPath(e0, e1, fastest=fastest)
            
            if path_e0_e1[0] is not None:
                for e in path_e0_e1[0]:
                    edges_reconstructed.append(e.getID())

        edges_reconstructed = [key for key, _group in groupby(edges_reconstructed)]
        
        duarouter_edges.append(edges_reconstructed)
        
    return duarouter_edges
    
    
def get_closest_edge_from_point(net, lat, lon, radius=1, autocorrect=True, return_dist=False):
    
    distances_and_edges = []
    dist, closest_edge = None, None
    
    x, y = net.convertLonLat2XY(lon, lat)
    
    if autocorrect:
        tries=90
    else:
        tries=1
    
    for try_ in range(tries):
        
        try:
            edges = net.getNeighboringEdges(x, y, try_)
        except:
            if try_ > tries:
                if return_dist:
                    return -1, 99999
                else:
                    return -1
            else:
                break
        else:
            if len(edges) > 0:
                break;
                
    if len(edges) > 0:
        try:
            #edges_and_dist = sorted([(dist, edge) for edge, dist in edges])
            edges_and_dist = sorted(edges, key = lambda x: x[1])
        except:
            return -1
        closest_edge = edges_and_dist[0][0]
        dist = edges_and_dist[0][1]
    else:
        if return_dist:
            return -1, 99999
        else:
            return -1

    if return_dist:
        return closest_edge.getID(), dist
    
    return closest_edge.getID()#, distances_and_edges, radius


def keep_th_consecutive(a, th=1):

    reps = [(k, sum(1 for _ in vs)) for k, vs in itertools.groupby(a)]
    reps = [elem[0] for elem in reps if elem[1]>th]

    return reps



def remove_loops_edge_list(el):

    edge_list = el
    loops = [(item, count) for item, count in collections.Counter(edge_list).items() if count > 1]

    for item, count in loops:
        indices = [i for i in range(len(edge_list)) if edge_list[i] == item]
        if len(indices)>1:
            edge_list = remove_a_loop(edge_list, indices[0], indices[-1])
        
    return edge_list


def remove_a_loop(edge_list, start_pos, end_pos):
    edges_no_loop = edge_list[:start_pos]+edge_list[end_pos:]  
    return edges_no_loop


def tdf_from_edgelist(edge_list, road_network):

    lngs, lats = [], []

    for edge_id in edge_list:

        x, y = road_network.getEdge(edge_id).getFromNode().getCoord()
        lon_from, lat_from = road_network.convertXY2LonLat(x, y)

        x, y = road_network.getEdge(edge_id).getToNode().getCoord()
        lon_to, lat_to = road_network.convertXY2LonLat(x, y)

        lngs.append(lon_from)
        lngs.append(lon_to)

        lats.append(lat_from)
        lats.append(lat_to)


    my_tdf = pd.DataFrame()

    my_tdf['uid'] = [1]*len(lngs)
    my_tdf['lng'] = lngs
    my_tdf['lat'] = lats
    my_tdf['datetime'] = [i for i in range(len(lngs))]

    traj_t = skmob.TrajDataFrame(my_tdf, latitude='lat', longitude='lng', 
                                                 user_id='uid', datetime='datetime')

    return traj_t


def eucl_dist(x, y):

    dist = np.linalg.norm(x - y)
    return dist

def e_spd(t1, t2, mdist, l_t1, l_t2, t2_dist):

    spd = sum([point_to_trajectory(t1[i1], t2, mdist[i1], t2_dist, l_t2) for i1 in range(l_t1)]) / l_t1
    return spd

def e_sspd(t1, t2):
   
    mdist = eucl_dist_traj(t1, t2)
    l_t1 = len(t1)
    l_t2 = len(t2)
    t1_dist = [eucl_dist(t1[it1], t1[it1 + 1]) for it1 in range(l_t1 - 1)]
    t2_dist = [eucl_dist(t2[it2], t2[it2 + 1]) for it2 in range(l_t2 - 1)]

    sspd = (e_spd(t1, t2, mdist, l_t1, l_t2, t2_dist) + e_spd(t2, t1, mdist.T, l_t2, l_t1, t1_dist)) / 2
    return sspd

def eucl_dist_traj(t1, t2):
   
    mdist = cdist(t1, t2, 'euclidean')
    return mdist

def point_to_trajectory(p, t, mdist_p, t_dist, l_t):
   
    dpt = min(
        [point_to_seg(p, t[it], t[it + 1], mdist_p[it], mdist_p[it + 1], t_dist[it]) for it in range(l_t - 1)])
    return dpt

def point_to_seg(p, s1, s2, dps1, dps2, ds):
 
    px = p[0]
    py = p[1]
    p1x = s1[0]
    p1y = s1[1]
    p2x = s2[0]
    p2y = s2[1]
    if p1x == p2x and p1y == p2y:
        dpl = dps1
    else:
        segl = ds
        x_diff = p2x - p1x
        y_diff = p2y - p1y
        u1 = (((px - p1x) * x_diff) + ((py - p1y) * y_diff))
        u = u1 / (segl * segl)

        if (u < 0.00001) or (u > 1):
            # closest point does not fall within the line segment, take the shorter distance to an endpoint
            dpl = min(dps1, dps2)
        else:
            # Intersecting point is on the line, use the formula
            ix = p1x + u * x_diff
            iy = p1y + u * y_diff
            dpl = eucl_dist(p, np.array([ix, iy]))

    return dpl


    
    
def match_with_fastest(points_traj, road_network, road_network_int, fr, to):
    
    edge_from, edge_to = road_network.getEdge(fr), road_network.getEdge(to)
    
    # FASTEST
    fast_edge = road_network.getOptimalPath(edge_from, edge_to, fastest=True)
    fast_edge_list = [e.getID() for e in fast_edge[0]]
    tdf_fast = tdf_from_edgelist(fast_edge_list, road_network)
    points_fast = tdf_fast[['lng','lat']].values
    
    sspd_fast = e_sspd(np.array(points_traj), np.array(points_fast))
    
    dist = sumolib.route.getLength(road_network_int, fast_edge_list)
    
    return fast_edge_list, sspd_fast, dist, "fast"


def match_with_shortest(points_traj, road_network, road_network_int, fr, to):
    
    edge_from, edge_to = road_network.getEdge(fr), road_network.getEdge(to)
    
    # SHORTEST
    short_edge = road_network.getShortestPath(edge_from, edge_to)
    short_edge_list = [e.getID() for e in short_edge[0]]
    tdf_short = tdf_from_edgelist(short_edge_list, road_network)
    points_short = tdf_short[['lng','lat']].values
    
    sspd_short = e_sspd(np.array(points_traj), np.array(points_short))
    
    dist = sumolib.route.getLength(road_network_int, short_edge_list)
    
    return short_edge_list, sspd_short, dist, "short"
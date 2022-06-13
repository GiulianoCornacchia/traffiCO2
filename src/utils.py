import skmob
import numpy as np
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from math import sqrt, sin, cos, pi, asin
import xml
from xml.dom import minidom
from itertools import groupby
import subprocess

import traci
import os
import sys


'''
Functions overview

'''



def compute_od_matrix(tdf, tessellation, traj_id="uid", self_loops=True):
    
    #compute origin and destination
    t_first = tdf.groupby(traj_id, as_index=False).first()
    t_last = tdf.groupby(traj_id, as_index=False).last()
    
    #concatenate the Os and Ds
    t_traj_od = pd.concat([t_first,t_last])
    t_traj_od = t_traj_od.sort_by_uid_and_datetime()
    t_traj_od = t_traj_od.reset_index(drop=True)
    
    #create the flows
    flows = t_traj_od.to_flowdataframe(tessellation, self_loops=self_loops)
    
    #create an empty matrix of dimension #tiles x #tiles
    od_matrix = np.zeros((len(tessellation),len(tessellation)))
    
    for o, d, flow in zip(flows['origin'], flows['destination'], flows['flow']):
        od_matrix[int(o)][int(d)] = flow
        
    return od_matrix


def create_dict_tile_edges(road_network, tessellation, exclude_roundabouts=False):
    
    lng_list, lat_list, edge_id_list = [], [], []

    edges_in_roundabouts = []

    if exclude_roundabouts:
        for r in road_network.getRoundabouts():
            for e in r.getEdges():
                edges_in_roundabouts.append(e)
    
    for edge in road_network.getEdges():

        edge_id = edge.getID()

        if edge_id not in edges_in_roundabouts:

            lng, lat = gps_coordinate_of_edge(road_network, edge_id)

            edge_id_list.append(edge_id)
            lng_list.append(lng)
            lat_list.append(lat)


    edge_coords = gpd.points_from_xy(lng_list, lat_list)
    
    gpd_edges = gpd.GeoDataFrame(geometry=edge_coords)
    gpd_edges['edge_ID'] = edge_id_list
    
    sj = gpd.sjoin(tessellation, gpd_edges)
    sj = sj.drop(["index_right", "geometry"], axis=1)
    
    res = sj.groupby(["tile_ID"])["edge_ID"].apply(list).to_dict()
    
    return res


def gps_coordinate_of_edge(net, edge_id):

    x, y = net.getEdge(edge_id).getFromNode().getCoord()
    lon, lat = net.convertXY2LonLat(x, y)

    return lon, lat


def create_mobility_demand(n_veichles, dict_tile_edges, od_matrix, road_network, filename,
                           timing="start", time_range=(0, 3601), random_seed=None,
                           show_progress=False, vehicles_background=None, threshold_km=1,
                           background_suffix="background_", vehicle_suffix="vehicle_", allow_self_tiles=True):
    
    departure_times = []
    
    # select n_veichles OD pairs from the od-matrix
    od_pairs, choices = create_traffic_from_matrix(od_matrix, dict_tile_edges, n_veichles, road_network, 
                                                threshold_km=threshold_km, allow_self_tiles=allow_self_tiles,
                                                show_progress=show_progress, random_seed=random_seed)
    
    dict_mobility_demand = {}

    for ind, el in enumerate(od_pairs):
        if timing == "start":
            def_time = 0
            departure_times.append(def_time)
        elif timing == "uniform_range":
            def_time = np.random.randint(time_range[0], time_range[1])
            departure_times.append(def_time)

        dict_mobility_demand[vehicle_suffix+str(ind)] = {'edges':el, 'time': def_time,
                              'via': False, 'number':1, 'dt':10}
    
    # create Background Traffic
    if vehicles_background is not None:

        if random_seed is not None:
                np.random.seed(random_seed)

        for ind0, elem in enumerate(vehicles_background):

            bg_t_start, bg_t_end = elem[1][0], elem[1][1]

            r_seed = np.random.randint(0,9999999)

            od_pairs_bg, choices_bg = create_traffic_from_matrix(od_matrix, dict_tile_edges, elem[0], road_network, 
                allow_self_tiles=allow_self_tiles, threshold_km=threshold_km, show_progress=False, random_seed=r_seed)

            for ind, el in enumerate(od_pairs_bg):
                def_time = np.random.randint(bg_t_start, bg_t_end+1)

                dict_mobility_demand[background_suffix+str(ind0)+"_"+str(ind)] = {'edges':el, 'time': def_time,
                              'via': False, 'number':1, 'dt':10}

    res = create_xml_flows(dict_mobility_demand, filename+".rou.xml")
    
    return od_pairs, departure_times, dict_mobility_demand


def create_xml_flows(dict_flows={}, filename=None, check_validity=True):
    
    # xml creation
    root = minidom.Document()
    xml = root.createElement("routes")
    xml.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    xml.setAttribute("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")
    root.appendChild(xml)

    #vehicle type(s)
    element = root.createElement("vType")
    element.setAttribute("id", "type1")
    element.setAttribute("accel", "2.6")
    element.setAttribute("decel", "4.5")
    element.setAttribute("sigma", "0.5")
    element.setAttribute("length", "5")
    element.setAttribute("maxSpeed", "70")
    xml.appendChild(element)

    valid_list = []
    invalid_list = []

    # _______ FLOW ________

    # flows e.g. <flow id="flow_x" type="type1" begin="0" end="0" 
    # number="1" from="edge_start" to="edge_end" via="e_i e_j e_k"/>

    # sort the dict
    dict_flows_time_sorted = dict(sorted(dict_flows.items(), key=lambda item: item[1]['time']))


    for traj_id in dict_flows_time_sorted.keys():

            edge_list = dict_flows_time_sorted[traj_id]['edges']
            edge_list = [e for e in edge_list if str(e)!="-1"]

            #remove consecutive duplicates
            edge_list = [x[0] for x in groupby(edge_list)]

            if check_validity:
                if not has_valid_route_traci(edge_list):
                    print("INVALID!")
                    invalid_list.append(traj_id)
                    continue

            valid_list.append(traj_id)

            intermediate_list = str(edge_list[1:-1]).replace(",","").replace("'","")[1:-1]
            start_edge = edge_list[0]
            end_edge = edge_list[-1]

            start_second = dict_flows_time_sorted[traj_id]['time']
            dt = dict_flows_time_sorted[traj_id]['dt']
            flow_num = dict_flows_time_sorted[traj_id]['number']
            via = dict_flows_time_sorted[traj_id]['via']

            col = "blue"
            #if 'rand' in traj_id:
            #    col = "red"

            element = root.createElement("flow")
            element.setAttribute("type", "type1")
            element.setAttribute("begin", str(start_second))
            element.setAttribute("end", str(start_second+dt))
            element.setAttribute("number", str(flow_num))
            element.setAttribute("from", start_edge)
            element.setAttribute("color", col)
            element.setAttribute("to", end_edge)
            if len(edge_list)>2:
                if via:
                    element.setAttribute("via", intermediate_list)
            element.setAttribute("id", traj_id)
            xml.appendChild(element)

    xml_str = root.toprettyxml(indent="\t")

    with open(filename, "w") as f:
        f.write(xml_str)

    return {'valid':valid_list, 'invalid': invalid_list}


def create_traffic_from_matrix(od_matrix, dict_tile_edges, n_vehicles, road_network, threshold_km=1.2, max_tries=100, 
                                choice="uniform", random_seed=None, allow_self_tiles=True, show_progress=True):
    
    if random_seed is not None:
        np.random.seed(random_seed)
        
    if show_progress or True:
         pbar = tqdm(total=n_vehicles) 
    
    # n_vehicles pairs in the form of (edge_start, edge_end)
    od_edges_list, choices_list = [], []
    
    #init traci for fast route validation
    try:
        init_traci()
    except traci.TraCIException:
        pass
    
    size = od_matrix.shape[0]
    
    #random choice of tile_start, tile_end
    weights = od_matrix.flatten()
    
    for v in range(n_vehicles):
        
        valid_od = False
        
        #selection of a single OD pair
        while not valid_od:

            tries = 0
            #random choice of origin and destination tile

            ind = random_weighted_choice(weights)
            #convert ind in row and cols
            tile_start, tile_end = str(int(ind/size)), str(ind%size)

            if not allow_self_tiles:
                while tile_start == tile_end:
                    ind = random_weighted_choice(weights)
                    tile_start, tile_end = str(int(ind/size)), str(ind%size)

            #list of edges in origin and dest
            edge_list_start = dict_tile_edges[tile_start]
            edge_list_end = dict_tile_edges[tile_end]

    
            while tries < max_tries:
                
                ind_start = np.random.randint(0, len(edge_list_start))
                ind_end = np.random.randint(0, len(edge_list_end))

                edge_start = edge_list_start[ind_start]
                edge_end = edge_list_end[ind_end]

                # compute distance here
                lon_o, lat_o = gps_coordinate_of_edge_avg(road_network, edge_start)
                lon_d, lat_d = gps_coordinate_of_edge_avg(road_network, edge_end)
                
                d_km = distance_earth_km({"lat":lat_o, "lon":lon_o}, {"lat":lat_d, "lon":lon_d})
                
                if d_km >= threshold_km:

                    if has_valid_route_traci([edge_start, edge_end]):
                        od_edges_list.append([edge_start, edge_end])
                        choices_list.append((int(ind/size), ind%size))
                        tries=0
                        if show_progress or True:
                            pbar.update(1)
                        valid_od = True
                        break
                else:
                    tries+=1

                if tries == max_tries:

                    edge_list_start_P = np.random.permutation(edge_list_start)
                    edge_list_end_P = np.random.permutation(edge_list_end)

                    for edge_start, edge_end in ((e1, e2) for e1 in edge_list_start_P for e2 in edge_list_end_P):
            
                        lon_o, lat_o = gps_coordinate_of_edge_avg(road_network, edge_start)
                        lon_d, lat_d = gps_coordinate_of_edge_avg(road_network, edge_end)

                        d_km = distance_earth_km({"lat":lat_o, "lon":lon_o}, {"lat":lat_d, "lon":lon_d})

                        if d_km >= threshold_km:
                            if has_valid_route_traci([edge_start, edge_end]):

                                od_edges_list.append([edge_start, edge_end])
                                choices_list.append((int(ind/size), ind%size))

                                if show_progress or True:
                                    pbar.update(1)
                                valid_od = True
                                break
                                         
    return od_edges_list, choices_list


def init_traci():
    
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    #Configuration
    sumo_binary = os.environ['SUMO_HOME']+"/bin/sumo"

    sumo_cmd = [sumo_binary, "-c", "../sumo_simulation_data/config_init_traci.sumocfg"]

    traci.start(sumo_cmd)
    traci.simulationStep()
    

def random_weighted_choice(weights):
        
    probabilities = weights/np.sum(weights)
    t =  np.random.multinomial(1, probabilities)
    pos_choice = np.where(t==1)[0][0]

    return pos_choice


def gps_coordinate_of_edge_avg(net, edge_id):

    x, y = net.getEdge(edge_id).getFromNode().getCoord()
    x1, y1 = net.getEdge(edge_id).getToNode().getCoord()
    lon, lat = net.convertXY2LonLat(x, y)
    lon1, lat1 = net.convertXY2LonLat(x1, y1)

    return (lon+lon1)/2, (lat+lat1)/2


def distance_earth_km(src, dest):
            
    lat1, lat2 = src['lat']*pi/180, dest['lat']*pi/180
    lon1, lon2 = src['lon']*pi/180, dest['lon']*pi/180
    dlat, dlon = lat1-lat2, lon1-lon2

    ds = 2 * asin(sqrt(sin(dlat/2.0) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2.0) ** 2))
    return 6371.01 * ds


def has_valid_route_traci(edge_list):

    for i in range(len(edge_list)-1):
        e_list = traci.simulation.findRoute(edge_list[i], edge_list[i+1]).edges

        if len(e_list)==0:
            return False    
        
    return True


def call_duarouter_command(command_str):
    
        p = subprocess.Popen(command_str, shell=True, stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT)
        retval = p.wait()
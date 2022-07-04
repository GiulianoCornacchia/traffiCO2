import uuid
import traci
import random
import os
import sys
import xml
import pandas as pd
from datetime import datetime



def create_sim_id():

    now = datetime.now()
    dt_string = now.strftime("%d_%m_%H_%M_%S")

    return dt_string



def config_start_sumo(net_file, route_file, opt_options=[], use_gui=True):

    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    #Configuration
    if use_gui:
        sumo_binary = os.environ['SUMO_HOME']+"/bin/sumo-gui" # sumo / sumo-gui
    else:
        sumo_binary = os.environ['SUMO_HOME']+"/bin/sumo" # sumo / sumo-gui


    '''
    When vehicles in SUMO are unable to move for some time they will be teleported to resolve dead-lock. 
    If this is not desired, sumo-option --ignore-junction-blocker <TIME> may be used to ignore vehicles which 
    are blocking the intersection on an intersecting lane after the specified time. 
    This can be used to model the real-life behavior of eventually finding a way around the offending 
    vehicle that is blocking the intersection.

    '''
    #def_options = [sumo_binary, "-c", config_file]

    def_options = [sumo_binary, "-n", net_file, "-r", route_file]

    options = def_options + opt_options

    #sumo_cmd = [sumo_binary, "-c", "./sumo_simulation_data/simple-sim.sumocfg"]"--time-to-teleport", 180  
    #sumo_cmd = [sumo_binary, "-c", config_file, "--ignore-junction-blocker", "30", "-W"]
    sumo_cmd = options
    #,"--no-internal-links", "True"]
    print(options)
    traci.start(sumo_cmd)

    return def_options, opt_options


def return_number_vehicles(route_filename):

    route_xml = xml.dom.minidom.parse(route_filename)

    n_flows = len(route_xml.getElementsByTagName('flow'))
    n_vehicles = len(route_xml.getElementsByTagName('vehicle'))

    return n_flows+n_vehicles


def return_net_and_route_filenames(config_file):

    config_doc = xml.dom.minidom.parse(config_file)

    path_net = config_doc.getElementsByTagName('net-file')[0].attributes['value'].value
    path_route = config_doc.getElementsByTagName('route-files')[0].attributes['value'].value

    return path_net, path_route



#Remember, the non-internal edges are the ones s.t. edge_id[0] != ":"
def filter_edges_for_route(internal=False):

    e_list = list(traci.edge.getIDList())

    if not internal:
        e_list = [e for e in e_list if e[0]!=":"]

    return e_list

def create_df_trajectories(uid_list, lat_list, lng_list, time_list, dict_measures=None):

    df = pd.DataFrame()

    df['uid'] = uid_list
    df['lat'] = lat_list
    df['lng'] = lng_list
    df['timestamp'] = time_list

    if dict_measures is not None:

        for k in dict_measures.keys():
            df[k] = dict_measures[k][1]

    return df

def create_df_edges_co2(dict_edge_co2):

    edge_col_list, co2_col_list = [], []

    for edge_id in dict_edge_co2:
        edge_col_list.append(edge_id)
        co2_col_list.append(dict_edge_co2[edge_id])

    df = pd.DataFrame()
    df['edge_id'] = edge_col_list
    df['total_co2'] = co2_col_list

    return df

def create_df_vehicles_co2(dict_vehicles_co2):

    vehicle_col_list, co2_col_list = [], []

    for v_id in dict_vehicles_co2:
        vehicle_col_list.append(v_id)
        co2_col_list.append(dict_vehicles_co2[v_id])

    df = pd.DataFrame()
    df['vehicle_id'] = vehicle_col_list
    df['total_co2'] = co2_col_list

    return df

def create_df_veichles_time(list_n_vehicles):
    df = pd.DataFrame()
    df['n_vehicles'] = list_n_vehicles

    return df

def create_df_vehicles_edges(dict_vehicle_edges, dict_final_vehicles_edge):

    for v in dict_vehicle_edges:
        edges = dict_vehicle_edges[v]
        for e in edges:
            dict_final_vehicles_edge[e]+=1

    d = pd.DataFrame.from_dict(dict_final_vehicles_edge, orient='index').reset_index()
    d = d.rename(columns = {'index':'edge_id', 0:'count'})

    return d 

def is_to_collect(id_vehicle, collect_mode):

    if collect_mode == "all" or (collect_mode=="rand" and "background" in id_vehicle) or (collect_mode=="real" and not "background" in id_vehicle):
        return True
    else:
        return False
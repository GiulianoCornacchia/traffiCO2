import os
import sys
import time
import traci
import time
import json
import pandas as pd
from sys import argv
from itertools import groupby
from xml.dom import minidom
from sim_utils_sumo import *


'''

run_sumo.py net_file route_file use_gui collect_mode_traj collect_mode_co2 save_dir folder_prefix [options] #[config_file]

INPUT ATTRIBUTES
_________________
use_gui: 1 use GUI / 0 Command Line

collect_mode_traj: value in {none, navigator, duarouter, all}: for which vehicles store the GPS points
collect_mode_co2: value in {none, navigator, duarouter, all}: for which vehicles store the edge-CO2 emissions
collect_travel_times: 
collect_vehicles_for_edge: 

save_dir: directory where to save the outputs
options: options to instantiate SUMO
config_file: path of the file withe the configuration

OUTPUTS
______

1 csv file containing the trajectories considering collect_mode_traj
1 csv file containing for each edge the CO2 emitted in that edge considering collect_mode_co2
1 json file containing a dictionary with some information about the simulation

'''
net_filename = argv[1]
route_filename = argv[2]
use_gui = True if int(argv[3])==1 else False

collect_mode_traj = argv[4]
collect_mode_co2 = argv[5]
collect_mode_travel_times = argv[6]
collect_mode_vehicles_for_edge = argv[7]

save_dir = argv[8]
folder_prefix = argv[9]
create_log = True

if len(argv)>9:
    opt_options = argv[10].split(" ")
else:
    opt_options = []

'''
if len(argv)>6:
    config_filename = argv[6]
else:
    config_filename = "./sumo_simulation_data/milan_config.sumocfg"
'''

# max steps 4 hour

max_steps = 4*60*60


collect_traj = False if collect_mode_traj == "none" else True
collect_co2 = False if collect_mode_co2 == "none" else True
collect_travel_times = False if collect_mode_travel_times == "none" else True
collect_vehicles_for_edge = False if collect_mode_vehicles_for_edge == "none" else True

#net_filename, route_filename = return_net_and_route_filenames(config_filename)

total_vehicles = return_number_vehicles(route_filename)

#create simulation ID %d_%m_%H_%M_%S
sim_id = create_sim_id()



#create directory for output
save_dir=save_dir+folder_prefix+"_"+sim_id
os.mkdir(save_dir)


print("\nSimulation id: "+sim_id)
print("\nParameters: \n")
print("Use GUI: "+str(use_gui))
print("Network file: "+net_filename)
print("Demand file: "+route_filename)
print("Optional options: "+str(opt_options))
print("Vehicles to simulate: "+str(total_vehicles)+"\n")

print("Collect traj: " +str(collect_traj))
if collect_traj:
    traj_df_filename = save_dir+"/trajectories.csv"
    print("Collect mode: "+collect_mode_traj)
    print("Output traj: "+traj_df_filename+"\n")

print("Collect CO2 (edges and vehicles): "+str(collect_co2))
if collect_co2:
    co2_edge_df_filename = save_dir+"/co2_edge.csv"
    co2_vehicle_df_filename = save_dir+"/co2_vehicle.csv"
    print("Collect mode: "+collect_mode_co2)
    print("Output CO2: "+co2_edge_df_filename+"\n")

print("Collect travel times: "+str(collect_travel_times))
if collect_travel_times:
    travel_times_filename = save_dir+"/traveltimes.json"
    print("Collect mode: "+collect_mode_travel_times)
    print("Output travel times: "+travel_times_filename+"\n")

print("Collect vehicles per edge: "+str(collect_vehicles_for_edge))
if collect_vehicles_for_edge:
    vehicles_edges_filename = save_dir+"/vehicles_edge.csv"
    print("Collect mode: "+collect_mode_vehicles_for_edge)
    print("Output vehicles per edge: "+vehicles_edges_filename+"\n")

df_n_vehicles_filename = save_dir+"/n_vehicles.csv"

print("\n\n")


# measures to collect
dict_measures = {'co2_mg_s':[traci.vehicle.getCO2Emission,[]],
                'fuel_ml_s':[traci.vehicle.getFuelConsumption,[]]}

dict_measures = {}

#simulation variables
n_teleports = 0
step = 0
vehicles_arrived = 0
uid_list, lat_list, lng_list, time_list = [], [], [], []
vehicles_active = []

#configuration the simulation
def_options, opt_options = config_start_sumo(net_filename, route_filename, opt_options=opt_options, use_gui=use_gui)

#travel_time dict
vehicles_travel_time = {}

#compute edge list for collecting emissions on edges
if collect_co2 or collect_vehicles_for_edge:
    edge_list = filter_edges_for_route(internal=True)

if collect_co2:
    dict_edge_co2 = {}
    for edge in edge_list:
        dict_edge_co2[edge]=0

    dict_vehicle_co2 = {}

#vehicles per edge
if collect_vehicles_for_edge:

    dict_vehicle_edges = {}
    dict_final_vehicles_edge = {}

    for edge in edge_list:
        dict_final_vehicles_edge[edge]=0

#start time
start_t = time.time()


while vehicles_arrived < total_vehicles and step < max_steps:

    traci.simulationStep()
    vehicle_list = traci.vehicle.getIDList()

    ''' Subscription (to implement)
    for veh_id in traci.simulation.getDepartedIDList():
        traci.vehicle.subscribe(veh_id, [traci.constants.VAR_POSITION])
    '''

    vehicles_active.append(len(vehicle_list))

    for vehicle in vehicle_list:

        if collect_travel_times:
            if is_to_collect(vehicle, collect_mode_travel_times):
                #print("A")
                if vehicle in vehicles_travel_time.keys():
                    vehicles_travel_time[vehicle]+=1
                else:
                    vehicles_travel_time[vehicle]=1
        
        if collect_traj:

            if is_to_collect(vehicle, collect_mode_traj):

                x, y = traci.vehicle.getPosition(vehicle)
                lon, lat = traci.simulation.convertGeo(x, y)

                uid_list.append(vehicle)
                lat_list.append(lat)
                lng_list.append(lon)
                time_list.append(step)

            # additional vehicle measures to store
            '''
            for k in dict_measures.keys():

                value = dict_measures[k][0](vehicle)
                dict_measures[k][1].append(value)
            '''
            #store the emissions made by the veichle on the current edge in the timestep
        
        edge_id = None

        if collect_co2:

            if is_to_collect(vehicle, collect_mode_co2):

                edge_id = traci.vehicle.getRoadID(vehicle)
                co2_emissions = traci.vehicle.getCO2Emission(vehicle)

                if edge_id!=-1:
                    dict_edge_co2[edge_id]+=co2_emissions
                else:
                    print("Edge -1 for vehicle: "+str(vehicle))

                if vehicle in dict_vehicle_co2.keys():
                    dict_vehicle_co2[vehicle]+=co2_emissions
                else:
                    dict_vehicle_co2[vehicle]=co2_emissions


        if collect_vehicles_for_edge:

            if is_to_collect(vehicle, collect_mode_vehicles_for_edge):

                if not collect_co2:
                    edge_id = traci.vehicle.getRoadID(vehicle)

                if vehicle in dict_vehicle_edges.keys():
                    
                    if dict_vehicle_edges[vehicle][-1]!=edge_id:
                            dict_vehicle_edges[vehicle].append(edge_id)
                else:
                    dict_vehicle_edges[vehicle] = [edge_id]



            #'''
    ''' Subscription (2 implement)
    if step==2:
        print(traci.vehicle.getAllSubscriptionResults())
    '''
    
    # collect number of teleported vehicles
    n_teleports+=traci.simulation.getStartingTeleportNumber()

    step += 1
    vehicles_arrived += traci.simulation.getArrivedNumber()




elapsed = time.time() - start_t
print("END OF THE SIMULATION **********************")
print("Execution time (s): "+str(round(elapsed, 2)))
print("Number of teleports: "+str(n_teleports))


#Trajectories dataset CSV
if collect_traj:
    df_traj = create_df_trajectories(uid_list, lat_list, lng_list, time_list, dict_measures)
    df_traj.to_csv(traj_df_filename, sep=",", index=False)


# Pollution datasets CSV
if collect_co2:

    df_edge_co2 = create_df_edges_co2(dict_edge_co2)
    df_edge_co2.to_csv(co2_edge_df_filename, sep=",", index=False)

    df_vehicle_co2 = create_df_vehicles_co2(dict_vehicle_co2)
    df_vehicle_co2.to_csv(co2_vehicle_df_filename, sep=",", index=False)

if collect_travel_times:
    a_file = open(travel_times_filename, "w")
    json.dump(vehicles_travel_time, a_file)
    a_file.close()


# number of vehicles at each time-step
df_n_vehicles = create_df_veichles_time(vehicles_active)
df_n_vehicles.to_csv(df_n_vehicles_filename, sep=",", index=False)


#vehicles per edges
if collect_vehicles_for_edge:
    df_vehicles_edges = create_df_vehicles_edges(dict_vehicle_edges, dict_final_vehicles_edge)
    df_vehicles_edges.to_csv(vehicles_edges_filename, sep=",", index=False)


# Create log file
if create_log:
    dict_log = {}
    dict_log["id"] = sim_id
    dict_log["net_filename"] = net_filename
    dict_log["route_filename"] = route_filename
    dict_log["def_options"] = def_options
    dict_log["opt_options"] = opt_options
    dict_log["execution_time_s"] = round(elapsed, 2)
    dict_log["n_vehicles"] = total_vehicles
    dict_log["n_teleports"] = n_teleports
    dict_log["n_steps"] = step
    dict_log["max_steps"] = max_steps

    a_file = open(save_dir+"/log.json", "w")
    json.dump(dict_log, a_file)
    a_file.close()

#close traci
traci.close()
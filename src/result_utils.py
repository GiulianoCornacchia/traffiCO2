import os
from glob import glob
import pandas as pd
import numpy as np
import json
from fitting import *


def create_dict_exps(folder_experiments, nav_str):

    dict_exps = {}

    folders= [f for f in os.listdir(folder_experiments) if not "ipynb_checkpoints" in f]

    for exp in folders:

        #retrieve sim parameters
        with open(folder_experiments+"/"+exp+"/log.json") as json_file:
            dict_json = json.load(json_file)

        demand_name = dict_json['route_filename'].split("/")[-1]
        pct_routed = demand_name.split(nav_str+"_")[1].split("_")[0]
        pct_non_routed = demand_name.split("dua_")[1].split("_")[0]
        n_rep = demand_name.split("rep_")[1].split("_")[0]

        key_de = pct_routed+"_"+pct_non_routed

        if key_de in dict_exps:
            dict_exps[key_de][n_rep] = exp
        else:
            dict_exps[key_de] = {n_rep: exp}
                
    return dict_exps


def merge(frames, on_columns):
    if not frames:
        return None
    if len(frames) == 1:
        return frames[0]
    out = frames[0]
    for df in frames[1:]:
        out = out.merge(df, on=on_columns)
    return out


def create_dict_results_co2(dict_exps, folder_experiments):

    dict_total_co2s = {}

    for fit_key in dict_exps.keys():

        map__simulation_type__filename = dict_exps[fit_key]

        map__simulation_type__df = {}
        for c_type, c_file_name in map__simulation_type__filename.items():
            c_df = pd.read_csv(glob(folder_experiments+c_file_name+"/co2_edge.csv")[0])
            map__simulation_type__df[c_type] = c_df.rename(columns={'total_co2': c_type})

        merged_df = merge([df for df in map__simulation_type__df.values()], on_columns='edge_id')

        #TOTAL CO2 EMISSIONS
        total_co2_tmp = []
        res = merged_df.sum()
        for k_co2 in res.keys():
            if k_co2 != "edge_id":
                total_co2_tmp.append(res[k_co2])

        dict_total_co2s[fit_key] = total_co2_tmp
        
    return dict_total_co2s




def create_dict_results_alpha(dict_exps, folder_experiments):

    dict_alphas_truncated = {}
        
    for fit_key in dict_exps.keys():

        map__simulation_type__filename = dict_exps[fit_key]

        map__simulation_type__df = {}
        for c_type, c_file_name in map__simulation_type__filename.items():
            c_df = pd.read_csv(glob(folder_experiments+c_file_name+"/co2_edge.csv")[0])
            map__simulation_type__df[c_type] = c_df.rename(columns={'total_co2': c_type})

        merged_df = merge([df for df in map__simulation_type__df.values()], on_columns='edge_id')

        #ALPHA (POWER-LAW EXPONENT)

        ## mapping each simulation to the emissions distribution
        map__simulation_type__distribution = {}
        for sim_type, c_df in map__simulation_type__df.items():
            map__simulation_type__distribution[sim_type] = np.array(c_df[sim_type])


        map__dist_type__fitting_results, map__dist_type__comparison_results = fit_powerlaw(map__simulation_type__distribution,
                                                                                           '',
                                                                                           'CO2', xmin=None,
                                                                                           list_distributions_to_fit=[
                                                                                               'truncated_power_law'],
                                                                                           plot_ccdf=False,
                                                                                           plot_pdf=False,
                                                                                           plot_xmin=False,
                                                                                           single_fit_to_plot='truncated_power_law', 
                                                                                           save_figures=False);

        # TRUNCATED POWER LAW  
        alpha_truncated_tmp = []
        for k in map__dist_type__fitting_results.keys():
            alpha_truncated = map__dist_type__fitting_results[k]['truncated_power_law']['alpha']
            alpha_truncated_tmp.append(alpha_truncated)

        dict_alphas_truncated[fit_key] = alpha_truncated_tmp
        
        
    return dict_alphas_truncated



def Lorenz(v, bins):
    total = float(np.sum(v))
    yvals = []
    for b in bins:
        bin_vals = v[v <= np.percentile(v, b)]
        bin_fraction = (np.sum(bin_vals) / total) * 100.0
        yvals.append(bin_fraction)
    # perfect equality area
    pe_area = np.trapz(bins, x=bins)
    # lorenz area
    lorenz_area = np.trapz(yvals, x=bins)
    gini_val = (pe_area - lorenz_area) / float(pe_area)
    return yvals, gini_val



def create_dict_results_gini(dict_exps, folder_experiments):
    
    dict_ginis = {}
    perc_routed = sorted([int(string_perc.split('_')[0]) for string_perc in dict_exps.keys()])
    
    for fit_key in dict_exps.keys():

        map__simulation_type__filename = dict_exps[fit_key]

        map__simulation_type__df = {}
        for c_type, c_file_name in map__simulation_type__filename.items():
            c_df = pd.read_csv(glob(folder_experiments+c_file_name+"/co2_edge.csv")[0])
            map__simulation_type__df[c_type] = c_df.rename(columns={'total_co2': c_type})

        merged_df = merge([df for df in map__simulation_type__df.values()], on_columns='edge_id')
        
        #return merged_df

        ## mapping each simulation to the emissions distribution
        map__simulation_type__distribution = {}
        for sim_type, c_df in map__simulation_type__df.items():
            map__simulation_type__distribution[sim_type] = np.array(c_df[sim_type])
        
        #return map__simulation_type__distribution
        
        # GINI
        list_ginis = [Lorenz(np.array(dist), perc_routed)[1] for key,dist in sorted(map__simulation_type__distribution.items())]
        

        dict_ginis[fit_key] = list_ginis
        
        
    return dict_ginis


def create_dict_exps_w(folder_experiments, nav_str):
    
    dict_exps = {}

    folders= [f for f in os.listdir(folder_experiments) if not "ipynb_checkpoints" in f]

    for exp in folders:

        #retrieve sim parameters
        with open(folder_experiments+"/"+exp+"/log.json") as json_file:
            dict_json = json.load(json_file)

        demand_name = dict_json['route_filename'].split("/")[-1]
        pct_routed = demand_name.split(nav_str+"_")[1].split("_")[0]
        pct_non_routed = demand_name.split("dua_")[1].split("_")[0]
        n_rep = demand_name.split("rep_")[1].split("_")[0]

        if pct_routed == "89":
            pct_routed = "90"

        if "w" in demand_name:
            w = demand_name.split("_")[0][1:]
        else:
            w = "5"

        key_de = pct_routed+"_"+pct_non_routed

        if w in dict_exps:
            if key_de in dict_exps[w]:
                dict_exps[w][key_de][n_rep] = exp
            else:
                dict_exps[w][key_de] = {}
                dict_exps[w][key_de][n_rep] = exp      
        else:
            dict_exps[w] = {key_de: {n_rep: exp}}
                
        return dict_exps



import skmob
import pandas as pd
import geopandas as gpd

def split_trajectories_in_tdf(tdf, stop_tdf):
    tdf_with_tid = tdf.groupby('uid').apply(_split_trajectories, stop_tdf)
    return tdf_with_tid.reset_index(drop=True)


def _split_trajectories(tdf, stop_tdf):
    c_uid = tdf.uid[:1].item()
    stop_tdf_current_user = stop_tdf[stop_tdf.uid == c_uid]
    if stop_tdf_current_user.empty:
        return
    else: 
        first_traj = [tdf[tdf.datetime <= stop_tdf_current_user.datetime[:1].item()]]
        last_traj = [tdf[tdf.datetime >= stop_tdf_current_user.leaving_datetime[-1:].item()]]
        all_other_traj = [tdf[(tdf.datetime >= start_traj_time) & (tdf.datetime <= end_traj_time)] for end_traj_time, start_traj_time in zip(stop_tdf_current_user['datetime'][1:], stop_tdf_current_user['leaving_datetime'][:-1])]
        all_traj = first_traj + all_other_traj + last_traj
        tdf_with_tid = pd.concat(all_traj)
        list_tids = [list(np.repeat(i, len(df))) for i, df in zip(range(1,len(all_traj)+1), all_traj)]
        list_tids_ravel = [item for sublist in list_tids for item in sublist]
        tdf_with_tid['tid'] = list_tids_ravel

        return tdf_with_tid
    

def filter_in_shape(tdf, shape, drop=True):
    
    points = gpd.points_from_xy(tdf.lng, tdf.lat)
    tdf['points'] = points
    tdf['isin'] = tdf['points'].apply(lambda x: shape.contains(x)[0])
    
    # ALL points inside
    at_least_one_outside = list(tdf.query("isin == False")['uid'].unique())
    trajs_all_inside = list(tdf[~tdf['uid'].isin(at_least_one_outside)]['uid'].unique())

    # AT LEAST one inside
    at_least_one_inside = list(tdf.query("isin == True")['uid'].unique())
    trajs_one_inside_small = list(tdf[tdf['uid'].isin(at_least_one_inside)]['uid'].unique())
    
    if drop:
        tdf = tdf.drop(["isin"], axis=1)
    
    return trajs_all_inside, trajs_one_inside_small


def segment_trajectories_area(x):
    
    tid=-1
    list_tids = []
    
    tmp = pd.DataFrame()
    
    tmp["isin"] = x["isin"]
    tmp["isin_prev"] = x["isin"].shift(+1)
    tmp["uid"] = x["uid"]
    tmp["uid_prev"] = x["uid"].shift(+1)

    for isin, isin_prev, uid, uid_prev in zip(tmp["isin"], tmp["isin_prev"], 
                                              tmp["uid"], tmp["uid_prev"]):

        if uid != uid_prev:
            tid+=1          
        elif isin != isin_prev:
            tid+=1
            
        list_tids.append(str(uid)+"_"+str(tid))
            
    return list_tids
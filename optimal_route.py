
__all__ = ['find']

# PREAMBLE

import numpy as np
from itertools import combinations, permutations #is the best not to use `as`?





392.2172595594006  # in kilometers

# FUNCTIONS

def find(points_cord):
    
    (dist_all,comb_idx,npoints) = compute_distances(points_cord)
    (tracks_all,ntracks) = compute_tracks(npoints)
    dist_min = loop_tracks(ntracks,npoints,tracks_all,comb_idx,dist_all)    

    print(dist_min)
    return

def compute_trip(points_cord):

    npoints = points_cord.shape[0]
    points_idx = np.arange(0, npoints, 1)
    comb_idx = np.array(list(combinations(points_idx, 2))) #is the best to convert from combinations to list to array?

    return (npoints,comb_idx)

def compute_distances(points_cord):

    from haversine import haversine, Unit

    #parameters
    CARTESIAN=1
    SPHERICAL=2

    npoints = points_cord.shape[0]
    points_idx = np.arange(0, npoints, 1)
    comb_idx = np.array(list(combinations(points_idx, 2))) #is the best to convert from combinations to list to array?
    comb_o_x = points_cord[comb_idx[:,0],0]
    comb_o_y = points_cord[comb_idx[:,0],1]
    comb_f_x = points_cord[comb_idx[:,1],0]
    comb_f_y = points_cord[comb_idx[:,1],1]

    #check if cartesian or spherical
    cord_type=...

    if cord_type==CARTESIAN:
        dist_all=np.sqrt((comb_f_x-comb_o_x)**2+(comb_f_y-comb_o_y)**2)    
    elif cord_type==SPHERICAL:
        lyon = (45.7597, 4.8422) # (lat, lon)
        paris = (48.8567, 2.3508)
        haversine(lyon, paris, Unit.METERS)
        #check: https://pypi.org/project/haversine/
        #and compute in matrix form!
    
    return (dist_all,comb_idx,npoints)

def compute_tracks(npoints):

    tracks_all_tmp=np.array(list(permutations(np.arange(1,npoints,1),npoints-1))) #without origin and end
    ntracks=tracks_all_tmp.shape[0]
    zeros_all=np.zeros([ntracks,1],dtype=int)
    tracks_all=np.concatenate((zeros_all,tracks_all_tmp,zeros_all),axis=1) #with origin and end

    return (tracks_all,ntracks)

def loop_tracks(ntracks,npoints,tracks_all,comb_idx,dist_all):

    dist_min=np.inf
    for ktrack in np.arange(0,ntracks,1):
        track_local=tracks_all[ktrack,:]
        dist_track=0
        for ktrip in np.arange(0,npoints,1):
            trip_local=np.sort(track_local[ktrip:ktrip+2])
            trip_idx = np.where((comb_idx == trip_local).all(axis=1))[0]
            dist_local=dist_all[trip_idx]
            dist_track=dist_track+dist_local
        if dist_track<dist_min:
            dist_min=dist_track

    return dist_min
######## BuzsakiSession.py ########
#gets information about a given Buzsaki session so that it can be imported
#to Neurodata Without Borders (nwb) format.
#
#
##################################

#record directory that houses the program
cwd = '/media/data/Dropbox (NewmanLab)/docs (1)/docs_Bryce/CMB2NWBproject/Test_Scripts'
target_data = '/media/data/Dropbox (NewmanLab)/BuzsakiData/Hippocampus/hc-3'
target_api = '/media/data/Dropbox (NewmanLab)/docs (1)/docs_Bryce/CMB2NWBproject/api-python'         
                #this can be changed in the final implementation if I house the nwb api with the Buzsaki data

import os

import numpy as np
import matplotlib.pyplot as plt
import h5py as h5
import csv
import itertools
from collections import OrderedDict
import xml.etree.ElementTree as ET



#a background function to sort lists in a human-friendly way
import re
def sort_nicely( l ):   
    """ Sort the given list in the way that humans expect.
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    l.sort( key=alphanum_key )



class Session():
    
    #create an instance of the Session class by passing a name of the desired session. This holds the Buzsaki session's data
    def __init__(self, sessionName):
        
        #### generate basic session info from metadata files ####
        os.chdir(target_data + '/Metadata/hc3-metadata-tables')
        sessions = np.recfromcsv('hc3-session.csv', delimiter=',', filling_values=np.nan, 
                                case_sensitive=True, deletechars='', replace_space=' ') #an array of all session data
        session = None
        for session in sessions:
            if sessionName == str(session[2]):
                break                                   #this saves the desired session as 'session'
        if session[0] == 1555 and sessionName != 'j01_maze05_M.001': 
            session = None
            raise ValueError('invalid session name')
        
        #metadata: session number
        self.sessionNum = session[0]
        
        #metadata: top-level group of the session
        self.topGroup = session[1]
        
        self.sessionName = session[2]
        
        #metadata: session stimulus
        self.sessionStim = session[3]
        
        #metadata: total time (s)
        self.sessionTime = session[5]
        
        #directory of the session
        self.sessionDir = target_data+'/'+self.topGroup+'/'+self.topGroup+'/'+self.sessionName
        
        #electrode position information - the positions of the session's electrodes in an array
        epos_data = np.genfromtxt('hc3-epos.csv', delimiter = ',', dtype = None)
        for epos in epos_data:
            if self.topGroup == str(epos[0]):
                break
        self.epos = epos
        for x in range (len(self.epos)-1, -1, -1):              #trim empty entries
            if self.epos[x] == '""':
                self.epos = np.delete(self.epos, x, None)
                x = x-1
        self.epos = np.delete(self.epos, [0,1], None)
        self.num_shanks = len(self.epos)
        
        #groupings of recording sites (eg. recording sites per shank)
        self.rec_site_group = []
        for x in range(self.num_shanks):
            for y in range(8):                                  #always a total of 8 recording sites per shank
                self.rec_site_group.append('p'+str(x))
                
        #relative depth map of recording sites
        num_sites = len(self.rec_site_group)
        self.rec_site_map = np.zeros((num_sites, 3))
        for x in range(num_sites):
            self.rec_site_map[x,0] = 0.00002*(x%8)              #20 umeter separation between sites
        self.rec_site_map = np.around(self.rec_site_map, 5)
        
        
        #### generate preliminary adaptation files (.csv, etc. ) needed by python from session files ####
        
        os.chdir(self.sessionDir)
        
        
        #### generate raw session data from session files ####
        
        #LED position data
        self.LED_posData = np.genfromtxt(self.sessionName+ '.whl', delimiter='\t')
        self.LED_posData = self.LED_posData * 0.01          #convert to meters
        
        #cluster timestamp data from each shank (as a list, data from each shank)
        self.res_files = []
        for i in os.listdir(os.getcwd()):                   #get each .res file
            if '.res' in i and i.index('.res') == len(sessionName):
                self.res_files.append(i)
        sort_nicely(self.res_files)
        self.cluster_times_list = []                        #create a list of data arrays from files
        for x in range(len(self.res_files)):
            array = np.genfromtxt(self.res_files[x])
            array = np.around(1./20000. * array, 10)        #converts to seconds
            self.cluster_times_list.append(array)
        
        #cluster number data from each shank (as a list, data from each shank)
        self.clu_files = []
        for i in os.listdir(os.getcwd()):                   #get each .clu file
            if '.clu' in i and i.index('.clu') == len(sessionName):
                self.clu_files.append(i)
        sort_nicely(self.clu_files)
        self.cluster_num_list = []
        for x in range(len(self.clu_files)):
            array = np.genfromtxt(self.clu_files[x])
            array = array[1:].astype(int)                   #trim the first line since it's not data
            self.cluster_num_list.append(array)
        
######## omitting this for now due to discrepancies in .fet file format for sessions ec016.234 and ec016.749
######## note that these discrepancies also exist in other sessions like ec013.965
#        #feature data from each shank (as a list, data from each shank)
#        self.fet_files = []
#        for i in os.listdir(os.getcwd()):                   #get each .fet file
#            if '.fet' in i and i.index('.fet') == len(sessionName):
#                self.fet_files.append(i)
#        sort_nicely(self.fet_files)
#        self.feature_data_list = []
#        for x in range(len(self.fet_files)):
#            features = np.genfromtxt(self.fet_files[x], skip_header=1, usecols = ((x) for x in range(24)))
#            self.feature_data_list.append(features)
            
        
        os.chdir(cwd)
        
        
    ######################################################################
    #### methods to manipulate the datasets and groups of the session ####
    ######################################################################

    def get_posTimestamps(self):
        '''
        Returns a set of pos_timestamps for a given session time (times for sessions are specified in:
        /home/sidious/Desktop/docs_Bryce_s/CMB2NWBproject/NWB_sample_data/Buzsaki/Metadata/hc3-metadata-tables/hc3-session.csv
        '''
    
        #an interval found in old Buzsaki-to-CMB matlab code; supposedly in https://crcns.org/files/data/hc3/crcns-hc3-data-description.pdf
        increment = 1/39.06
        
        pos_timestamps = np.empty([int(self.sessionTime/increment)+10])  #add 10 to ensure timestamps is longer than data
                                                                    #so that timestamps, rather than data, gets trimmed in the posDict
        
        for i in range(0, pos_timestamps.size):
            pos_timestamps[i] = increment *i
        return pos_timestamps
        
        
    def get_posDict(self):
        '''
        Creates a python dictionary of the session position timestamps and position data.
        Returns three dictionaries, one corresponding to each LED, and one corresponding to calculated real position
        '''
    
        pos_timestamps = self.get_posTimestamps()
        
        dict_1 = {}                                                                 #dict for LED1 positions
        #####*************
        for i in range (    int(self.LED_posData.shape[0]   *.01)):                 #here I assume that there are equal #s of x and y positions
            if self.LED_posData[i,0] >= 0 and self.LED_posData[i,1] >= 0:           #trim out the invalid position values (-1)
                dict_1.update({pos_timestamps[i]: self.LED_posData[i,:2]})          #unsorted dict
        dict_1 = OrderedDict(sorted(dict_1.items(), key=lambda t: t[0]))            #sorted dict
        
        dict_2 = {}                                                                 #dict for LED2 positions
        #####************************************************************
        for i in range (    int(self.LED_posData.shape[0]   *.01)):
            if self.LED_posData[i,2] >= 0 and self.LED_posData[i,3] >= 0:
                dict_2.update({pos_timestamps[i]: self.LED_posData[i,2:]})          #unsorted dict
        dict_2 = OrderedDict(sorted(dict_2.items(), key=lambda t: t[0]))            #sorted dict
        
        print '***Calculating intermediate rat position - this may take some time.***'
        dict_3 = {}
        for i in range (len(pos_timestamps)):
            if pos_timestamps[i] not in dict_1.keys(): continue
            if pos_timestamps[i] not in dict_2.keys(): continue
            dict_3.update({pos_timestamps[i]:[
                            round((round(dict_1[pos_timestamps[i]][0], 10)\
                            + round(dict_2[pos_timestamps[i]][0], 10))/2, 10),\
                            round((round(dict_1[pos_timestamps[i]][1], 10)\
                            + round(dict_2[pos_timestamps[i]][1], 10))/2, 10)\
            ]})
        dict_3 = OrderedDict(sorted(dict_3.items(), key=lambda t: t[0]))
        
        print '***Done calculating position.***\n'
        return (dict_1,dict_2,dict_3)
        
        
    def get_UnitTimes(self, x):
        
        times = {}
#        for x in range(len(self.cluster_num_list)):
        a = self.cluster_num_list[x]
        u = np.unique(a)                                         #list of different cluster numbers for current shank
        indices = [np.argwhere(i==a) for i in np.unique(a)]   #list of indices of each cluster firing in the .clu data
        for y in range(len(u)):                                     #for each cluster in current shank
            shank_cluster_indices = indices[y]
            shank_times = self.cluster_times_list[x]
            t = shank_times[shank_cluster_indices]                  #find only the times that correspond to the current cluster firing
            times.update({u[y]: np.squeeze(t, axis=(1,))})       #np.squeeze changes from 2D to 1D
        return (u, times)
        
    def load_LFPdata(self):
        '''
        Loads LFP data into two dictionaries: one with all LFP data, and another
        with LFP data from only active sites.
        Dictionary format: keys are site numbers (0-indexed); values are numpy arrays of data
        '''
        
        os.chdir(self.sessionDir)
        
        tree = ET.parse(self.sessionName+ '.xml')
        root = tree.getroot()
        
        #create a dictionary with general info related to LFP data acquisition
        self.LFP_meta_dict = {}
        for i in root.find('acquisitionSystem'):
            self.LFP_meta_dict.update({i.tag: i.text})
        for i in root.find('fieldPotentials'):
            self.LFP_meta_dict.update({i.tag: i.text})
        
        #match the shanks with their active sites
        self.active_groups_channels = {}; group = []; count = 0; shanks = []
        for i in root.find('anatomicalDescription').find('channelGroups'):
            for j in i:
                group.append(int(j.text))
            self.active_groups_channels.update({count: group})
            shanks.append(count)
            count = count+1
            group = []
        active_channels = list(itertools.chain(*self.active_groups_channels.values()))      #flattens the active_groups_channels dict into list
        
        nChannels = int(root.find('acquisitionSystem').find('nChannels').text)
        
        #match the shanks with all of their sites
        self.groups_channels = {}
        for x in range(self.num_shanks):
            self.groups_channels.update({x: [y for y in range(8*x, 8*(x+1))]})

        print '***Loading LFP data - this may take some time.***'
        with open(self.sessionName+ '.eeg', 'rb') as f:
            raw_LFP = np.fromfile(f, np.int16).reshape((-1, nChannels))
            f.close()
        raw_LFP = np.around(3333333333./10921799911533422.*raw_LFP, 11)
                                    #this value facilitates a conversion from raw LFP to volts;
                                    #obtained from comparison of sample LFP data and values in volts
        
        #get LFP data as a dictionary to preserve channel/site number
        self.LFP = {}
        for x in range(raw_LFP.shape[1]):
            self.LFP.update({x: raw_LFP[:,x]})
        
        #get only active channels (ie. only those specified in the .xml)
        self.active_LFP = {}
        for i in active_channels:
            self.active_LFP.update({i: self.LFP[i]})
        self.active_LFP = OrderedDict(sorted(self.active_LFP.items(), key=lambda t: t[0]))  #sort the sites
        
        self.LFP_timestamps = [x/1250. for x in range(len(raw_LFP[:,0]))]
        
        os.chdir(cwd)
        print '***Done loading LFP data.***\n'

    def get_shankLFP(self, shank):
        '''
        Gets the LFP data for a given shank. Bear in mind that the returned
        data is in dict format and is hence unsorted.
        '''
        
        LFP_slice = {}
        curr_channels = self.groups_channels[shank]
        for i in curr_channels:
            LFP_slice.update({i: self.LFP[i]})
            if i not in self.active_LFP.keys():
                print 'WARNING: data loaded, but site %s is not an active site - '\
                      'perhaps choose another shank for fully reliable data' %i
        return LFP_slice
        
        
    def get_CSD(self, shank):
        '''
        Performs CSD analysis on a given shank's lfp data.
        '''
        
        os.chdir(self.sessionDir)
        
        #Adapted from http://fmatoolbox.sourceforge.net/API/FMAToolbox/Analyses/CSD.html
        
        if shank not in self.active_groups_channels:
            raise ValueError('requested shank does not have any valid sites or does not exist')
        numSites = len(self.active_groups_channels[shank])
#        lfp = np.empty([len(self.LFP_timestamps), numSites])
        
        if numSites != 8: print 'only %s valid sites on this shank (should be 8); CSD will be skewed' %numSites
        
        x = 0
        for i in self.active_groups_channels[shank]:
            if x == 0:                                          #populate lfp with the first site's data
                lfp = self.active_LFP[i]
                lfp = lfp.reshape(-1,1)
            else:                                               #concatenate the data from the remaining sites
                target = self.active_LFP[i]
                target = np.reshape(target, (-1,1))
                lfp = np.concatenate((lfp, target), axis=1)
            x = x + 1
        mean = lfp.mean(axis=0)
        mean = mean.reshape(1,-1)
        lfp = lfp - np.tile(mean, (len(self.LFP_timestamps), 1))
        d = -np.diff(lfp,2,1)
        
        os.chdir(cwd)
        
        return d
        
    #a perhaps faster version to calculate CSD - uses get_shankLFP instead of
    #explicitly getting the shank's LFP like get_CSD above
    def get_CSD2(self, shank):
        '''
        Performs CSD analysis on a given shank's lfp data.
        '''
        
        os.chdir(self.sessionDir)
        
        #Adapted from http://fmatoolbox.sourceforge.net/API/FMAToolbox/Analyses/CSD.html
        
        if shank not in self.active_groups_channels:
            raise ValueError('requested shank does not have any valid sites or does not exist')
        numSites = len(self.active_groups_channels[shank])
        
        if numSites != 8: print 'only %s valid sites on this shank (should be 8); CSD will be skewed' %numSites
        
        lfp_dict = self.get_shankLFP(shank)
        x = 0
        for i in lfp_dict:
            if x == 0:
                lfp = lfp_dict[i]
                lfp = lfp.reshape(-1,1)
            else:
                target = lfp_dict[i]
                target = np.reshape(target, (-1,1))
                lfp = np.concatenate((lfp, target), axis=1)
            x = x + 1
        mean = lfp.mean(axis=0)
        mean = mean.reshape(1,-1)
        lfp = lfp - np.tile(mean, (len(self.LFP_timestamps), 1))
        d = -np.diff(lfp,2,1)
        
        os.chdir(cwd)
        
        return d
        
    def cleanup(self):
        '''
        Removes any files generated by the program for python compatibility.
        '''
        
        print 'Cleaning up files'
        
        os.chdir(self.sessionDir)
        
        
        print 'Done cleaning files'

session = Session('ec013.156')
session.load_LFPdata()
csd = session.get_CSD(4)


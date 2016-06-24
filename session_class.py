######## session_class.py ########
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

import numpy
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
        sessions = numpy.recfromcsv('hc3-session.csv', delimiter=',', filling_values=numpy.nan, 
                                case_sensitive=True, deletechars='', replace_space=' ') #an array of all session data
        session = None
        for session in sessions:
            if sessionName == str(session[2]):
                break                                   #this saves the desired session as 'session'
        if session[0] == 1555 and sessionName != 'j01_maze05_M.001': 
            session = None
            raise ValueError('invalid session name')    #checks to see if a session was chosen
        
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
        epos_data = numpy.genfromtxt('hc3-epos.csv', delimiter = ',', dtype = None)
        for epos in epos_data:
            if self.topGroup == str(epos[0]):
                break
        self.epos = epos
        for x in range (len(self.epos)-1, -1, -1):              #trim empty entries
            if self.epos[x] == '""':
                self.epos = numpy.delete(self.epos, x, None)
                x = x-1
        self.epos = numpy.delete(self.epos, [0,1], None)
        self.num_shanks = len(self.epos)
        
        #groupings of recording sites (eg. per shank)
        self.rec_site_group = []
        for x in range(self.num_shanks):
            for y in range(8):                  #always a total of 8 recording sites per shank
                self.rec_site_group.append('p'+str(x))
                
        #relative depth map of recording sites
        num_sites = len(self.rec_site_group)
        self.rec_site_map = numpy.zeros((num_sites, 3))
        for x in range(num_sites):
            self.rec_site_map[x,0] = 0.00002*(x%8)
        self.rec_site_map = numpy.around(self.rec_site_map, 5)
        
        
        #### generate preliminary adaptation files (.csv, etc. ) needed by python from session files ####
        
        os.chdir(self.sessionDir)
        
#        #change SESSIONNAME.whl position data to numpy-friendly .csv format
#        f = open(self.sessionName+'.whl', 'rb')
#        reader = csv.reader(f, delimiter = '\t')
#        g = open(self.sessionName+'.whl.csv', 'wb')
#        writer = csv.writer(g)
#        writer.writerows(reader)
#        f.close()
#        g.close()        
        
        #### generate raw session data from session files ####
        
        #LED position data
        self.LED_posData = numpy.genfromtxt(self.sessionName+ '.whl', delimiter='\t')
        self.LED_posData = self.LED_posData * 0.01        #convert to meters
        
#        #LED position data
#        self.LED_posData = numpy.genfromtxt(self.sessionName+'.whl.csv', delimiter = ',')
#        self.LED_posData = self.LED_posData * 0.01
        
        #cluster timestamp data from each shank (as a list, data from each shank)
        self.res_files = []
        for i in os.listdir(os.getcwd()):                   #get each .res file
            if '.res' in i and i.index('.res') == len(sessionName):
                self.res_files.append(i)
        sort_nicely(self.res_files)
        self.cluster_times_list = []                        #create a list of data arrays from files
        for x in range(len(self.res_files)):
            array = numpy.genfromtxt(self.res_files[x])
            array = numpy.around(1./20000. * array, 10)     #converts to seconds
            self.cluster_times_list.append(array)
        
        #cluster number data from each shank (as a list, data from each shank)
        self.clu_files = []
        for i in os.listdir(os.getcwd()):                   #get each .clu file
            if '.clu' in i and i.index('.clu') == len(sessionName):
                self.clu_files.append(i)
        sort_nicely(self.clu_files)
        self.cluster_num_list = []
        for x in range(len(self.clu_files)):
            array = numpy.genfromtxt(self.clu_files[x])
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
#            features = numpy.genfromtxt(self.fet_files[x], skip_header=1, usecols = ((x) for x in range(24)))
#            self.feature_data_list.append(features)
            
        
        os.chdir(cwd)
        
        
    ######################################################################
    #### methods to manipulate the datasets and groups of the session ####
    ######################################################################

    def make_pos_timestamps(self):
        '''
        creates a set of pos_timestamps for a given session time (times for sessions are specified in:
        /home/sidious/Desktop/docs_Bryce_s/CMB2NWBproject/NWB_sample_data/Buzsaki/Metadata/hc3-metadata-tables/hc3-session.csv
        '''
    
        #an interval found in old Buzsaki-to-CMB matlab code; supposedly in https://crcns.org/files/data/hc3/crcns-hc3-data-description.pdf
        increment = 1/39.06
        
        pos_timestamps = numpy.empty([int(self.sessionTime/increment)+10])  #I add 10 to ensure timestamps is longer than data
                                                                    #(so that timestamps gets trimmed in the structuredDict rather than data)
        
        for i in range(0, pos_timestamps.size):
            pos_timestamps[i] = increment *i

        #the total time ends up being a bit longer than the given time; I verified this through testing, so somehow
            #the exact lengths of the sessions given must not be quite so exact (also consider 
                #the 'blank' data at the start and end of the session which must contribute to this)
        return pos_timestamps
        
        
    def make_posDict(self):
        '''
        Makes a python dictionary of the session position timestamps and position data.
        Returns three dictionaries, one corresponding to each LED, and one corresponding to calculated real position
        '''
    
        pos_timestamps = self.make_pos_timestamps()
        
        dict_1 = {}                                                         #dict for LED1 positions
        #####*************
        for i in range (    int(self.LED_posData.shape[0]   *1)):     #here I assume that there are equal #s of x and y positions
            if self.LED_posData[i,0] >= 0 and self.LED_posData[i,1] >= 0:         #trim out the invalid position values (-1)
                dict_1.update({pos_timestamps[i]: self.LED_posData[i,:2]})          #unsorted dict
        dict_1 = OrderedDict(sorted(dict_1.items(), key=lambda t: t[0]))    #sorted dict; could I combine these two steps?
        
        dict_2 = {}                                                         #dict for LED2 positions
        #####************************************************************
        for i in range (    int(self.LED_posData.shape[0]   *1)):
            if self.LED_posData[i,2] >= 0 and self.LED_posData[i,3] >= 0:
                dict_2.update({pos_timestamps[i]: self.LED_posData[i,2:]})          #unsorted dict
        dict_2 = OrderedDict(sorted(dict_2.items(), key=lambda t: t[0]))    #sorted dict
        
        print '***Calculating intermediate rat position - this may take some time.***'
        dict_3 = {}
        for i in range (len(pos_timestamps)):
            if pos_timestamps[i] not in dict_1.keys(): continue
            if pos_timestamps[i] not in dict_2.keys(): continue
            dict_3.update({pos_timestamps[i]: [round((round(dict_1[pos_timestamps[i]][0], 10) + round(dict_2[pos_timestamps[i]][0], 10))/2, 10), round((round(dict_1[pos_timestamps[i]][1], 10) + round(dict_2[pos_timestamps[i]][1], 10))/2, 10)]})
        dict_3 = OrderedDict(sorted(dict_3.items(), key=lambda t: t[0]))
        
#        #testing for dict_3 errors
#        with open('dict_1.csv', 'wb') as f:
#            w = csv.writer(f)
#            w.writerows(dict_1.items())
#            f.close()
#        with open('dict_2.csv', 'wb') as f:
#            w = csv.writer(f)
#            w.writerows(dict_2.items())
#            f.close()
#        #
        
        print '***Done calculating position.***\n'
        return (dict_1,dict_2,dict_3)
        
        
    def get_unit_times(self, x):
        
        times = {}
#        for x in range(len(self.cluster_num_list)):
        a = self.cluster_num_list[x]
        u = numpy.unique(a)                                         #list of different cluster numbers for current shank
        indices = [numpy.argwhere(i==a) for i in numpy.unique(a)]   #list of indices of each cluster firing in the .clu data
        for y in range(len(u)):                                     #for each cluster in current shank
            shank_cluster_indices = indices[y]
            shank_times = self.cluster_times_list[x]
            t = shank_times[shank_cluster_indices]                  #find only the times that correspond to the current cluster firing
            times.update({u[y]: numpy.squeeze(t, axis=(1,))})       #numpy.squeeze changes from 2D to 1D
        return (u, times)
        
    def load_LFPdata(self):
        '''
        Loads LFP data for all channels into numpy format.
        '''
        
        os.chdir(self.sessionDir)
        
        tree = ET.parse(self.sessionName+ '.xml')
        root = tree.getroot()
        
        self.LFP_meta_dict = {}
        for i in root.find('acquisitionSystem'):
            self.LFP_meta_dict.update({i.tag: i.text})
        i = root.find('fieldPotentials')
        self.LFP_meta_dict.update({i.tag: i.text})
        
        
        #find the active recording shanks and their channels
        ###keep in mind that this includes the last "shank" that has one channel - this is presumably a timestamp or something
        ###this isn't functionally a problem since I don't write any data from that "shank" in  write_nwb()
        self.active_groups_channels = {}; group = []; count = 0; shanks = []
        for i in root.find('anatomicalDescription').find('channelGroups'):
            for j in i:
                group.append(int(j.text))
            self.active_groups_channels.update({count: group})
            shanks.append(count)
            count = count+1
            group = []
        #find only the active channels
        active_channels = list(itertools.chain(*self.active_groups_channels.values()))      #flattens the active_groups_channels dict into list
        
        nChannels = int(root.find('acquisitionSystem').find('nChannels').text)
        
        #I do not currently need the following variables:
#        channels = numpy.array([active_channels])        #we're going to be reading/writing all active channels
#        lfp_rate = int(root.find('fieldPotentials').find('lfpSamplingRate').text)
#        precision = 'int16'
#        sampleSize = 2              #hardcoded since this is the default precision for the LFP data
        
#        with open(self.sessionName+ '.eeg', 'rb') as f:
#            f.seek(0,2)
#            last_pos = f.tell()
#            
#            #in case all channels do not have the same number of samples
#            maxNSamplesPerChannel = last_pos/nChannels/sampleSize
#            nSamplesPerChannel = maxNSamplesPerChannel
#            
#            maxSamplesPerChunk = 10000
#            nSamples = nSamplesPerChannel*nChannels
##            if nSamples <= maxSamplesPerChunk:
##                data = self.LoadChunk(nChannels, channels, nSamples, precision)
##                print data.shape
##            data = self.LoadChunk(nChannels, channels, nSamples, precision)
#            f.close()

        print '***Loading LFP data - this may take some time.***'
        with open(self.sessionName+ '.eeg', 'rb') as f:
            self.all_LFP_data = numpy.fromfile(f, numpy.int16).reshape((-1, nChannels))
            f.close()
        self.all_LFP_data = numpy.around(3333333333./10921799911533422. * self.all_LFP_data, 11)
                                    #this value is a conversion factor from raw LFP to volts
                                    #obtained from comparison of sample LFP data and values in volts
            
        #get LFP data from only the active channels
        self.LFP_data = numpy.empty([self.all_LFP_data.shape[0], int(active_channels[-1])+1])        #assumes the same number of lines exists for all channels
        for i in active_channels:
            self.LFP_data[:, i] = self.all_LFP_data[:, i]
        
        #above, 'self.LFP_data' will have indices for all active/inactive channels, but will have 0.0 for all
        #inactive entries
        
        data = self.access_shankLFP(shanks)
        self.LFP_timestamps = [x/1250. for x in range(len(data[0]))]
        print '***Done loading LFP data.***\n'
        
        os.chdir(cwd)
        
        return data
        
    def access_shankLFP(self, shank):
        '''
        Accesses the LFP data for a shank(s) specified by the "shank" integer/list parameter.
        Called by load_LFPdata() but can also be called by user to access specific sets.
        '''
        
        os.chdir(self.sessionDir)
        
        if type(shank) is int:
            curr_channels = self.active_groups_channels[shank]
            LFP_data_slice = numpy.empty([self.LFP_data.shape[0], len(curr_channels)])
            for x in range(len(curr_channels)):
                LFP_data_slice[:, x] = self.LFP_data[:, curr_channels[x]]
            os.chdir(cwd)
            return LFP_data_slice
        
        elif type(shank) is list:
            curr_channels = [self.active_groups_channels[x] for x in shank]
            LFP_data_slice_list = []
            for y in range(len(shank)):
                LFP_data_slice = numpy.empty([self.LFP_data.shape[0], len(curr_channels[y])])
                for z in range(len(curr_channels[y])):
                    LFP_data_slice[:, z] = self.LFP_data[:, curr_channels[y][z]]
                LFP_data_slice_list.append(LFP_data_slice)
            os.chdir(cwd)
            return LFP_data_slice_list
            
        #to save LFP data as a file: do "numpy.savetxt('name', self.access_shankLFP(X), fmt='%.10f', delimiter=',')
                                                                    #'X' is the shank you want data from

    def adjusted_LFP(self):
        '''
        Gets LFP data in a format usable for CSD calculation.
        '''
        
        os.chdir(self.sessionDir)
        
        curr_channels = [self.active_groups_channels[x] for x in range(session.num_shanks)]
        for y in range(session.num_shanks):
            LFP_data_slice = numpy.empty([session.LFP_data.shape[0], len(curr_channels[y])])
            for z in range(len(curr_channels[y])):
                LFP_data_slice[:, z] = session.LFP_data[:, curr_channels[y][z]]
            if y == 0:
                active_LFPdata = LFP_data_slice
            else:
                active_LFPdata = numpy.concatenate((active_LFPdata, LFP_data_slice), axis=1)
        
        os.chdir(cwd)
        
        return active_LFPdata
        
    def CSD(self, LFP):
        '''
        Performs CSD analysis on given LFP data.
        '''
        
        os.chdir(self.sessionDir)
        
        #Adapted from http://fmatoolbox.sourceforge.net/API/FMAToolbox/Analyses/CSD.html
        mean = LFP.mean(axis=0)
        mean = mean.reshape(1,-1)
        LFP = LFP - numpy.tile(mean, (len(self.LFP_timestamps), 1))
        d = -numpy.diff(LFP,2,1)
        
        os.chdir(cwd)
        
        return d
        
    def cleanup(self):
        '''
        Removes any files generated by the program for python compatibility.
        '''
        
        print 'Cleaning up files'
        
        os.chdir(self.sessionDir)
        
        
        print 'Done cleaning files'



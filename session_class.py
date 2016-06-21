#record directory that houses the program
cwd = '/media/data/Dropbox (NewmanLab)/docs (1)/docs_Bryce/CMB2NWBproject/Test_Scripts'
target_data = '/media/data/Dropbox (NewmanLab)/BuzsakiData/Hippocampus/hc-3'
target_api = '/media/data/Dropbox (NewmanLab)/docs (1)/docs_Bryce/CMB2NWBproject/api-python'         
                #this can be changed in the final implementation if I house the nwb api with the Buzsaki data

import os

import numpy
import h5py as h5
import csv
import itertools
from collections import OrderedDict
import xml.etree.ElementTree as ET
#from decimal import *

os.chdir(target_api)
from nwb import nwb_file
from nwb import utils
from nwb import nwb_core
os.chdir(cwd)


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
        
        #feature data from each shank (as a list, data from each shank)
        self.fet_files = []
        for i in os.listdir(os.getcwd()):                   #get each .fet file
            if '.fet' in i and i.index('.fet') == len(sessionName):
                self.fet_files.append(i)
        sort_nicely(self.fet_files)
        self.feature_data_list = []
        for x in range(len(self.fet_files)):
            features = numpy.genfromtxt(self.fet_files[x], skip_header=1, usecols = ((x) for x in range(24)))
            self.feature_data_list.append(features)
            
        
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
        if len(dict_1.keys()) <= len(dict_2.keys()):        #use the LED data with the fewest valid positions as reference to ensure proper position calculations
            reference_dict = dict_1
        else: reference_dict = dict_2
#        for i in range (len(reference_dict.keys())):
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
            all_LFP_data = numpy.fromfile(f, numpy.int16).reshape((-1, nChannels))
            f.close()
            
        #get LFP data from only the active channels
        self.LFP_data = numpy.empty([all_LFP_data.shape[0], int(active_channels[-1])+1])
        for i in active_channels:
            self.LFP_data[:, i] = all_LFP_data[:, i]
        self.LFP_data = numpy.around(3333333333./10921799911533422. * self.LFP_data, 11)
                                    #this value is a conversion factor from raw LFP to volts
                                    #obtained from comparison of sample LFP data and values in volts
        
        data = self.access_LFPdata(shanks)
        print '***Done loading LFP data.***\n'
        return data
        
    def access_LFPdata(self, shank):
        '''
        Accesses the LFP data for a shank(s) specified by the "shank" integer/list parameter.
        Called by load_LFPdata() but can also be called by user to access specific sets.
        '''
        
        if type(shank) is int:
            curr_channels = self.active_groups_channels[shank]
            LFP_data_slice = numpy.empty([self.LFP_data.shape[0], len(curr_channels)])
            for x in range(len(curr_channels)):
                LFP_data_slice[:, x] = self.LFP_data[:, curr_channels[x]]
            return LFP_data_slice
        
        elif type(shank) is list:
            curr_channels = [self.active_groups_channels[x] for x in shank]
            LFP_data_slice_list = []
            for y in range(len(shank)):
                LFP_data_slice = numpy.empty([self.LFP_data.shape[0], len(curr_channels[y])])
                for z in range(len(curr_channels[y])):
                    LFP_data_slice[:, z] = self.LFP_data[:, curr_channels[y][z]]
                LFP_data_slice_list.append(LFP_data_slice)
            return LFP_data_slice_list
            
        #to save LFP data as a file: do "numpy.savetxt('name', self.access_LFPdata(X), fmt='%.10f', delimiter=',')
                                                                    #'X' is the shank you want data from
        
    def access_LFPmetadata(self):
        '''
        Accesses the misc. metadata fields regarding the session's LFP data.
        '''
        
               
        
    def cleanup(self):
        '''
        Removes any files generated by the program for python compatibility.
        '''
        
        print 'Cleaning up files'
        
        os.chdir(self.sessionDir)
        
        
        print 'Done cleaning files'
        
        
def write_nwb(sessionName):

    #numpy.savetxt('nexttestdata', data, fmt = '%.6e', delimiter=',')   #this is the format that preserves precision
    
    ######################
    ### WRITE TO FILE ####
    ######################
    
    os.chdir(target_api)        #location to write the .nwb file to
    print 'writing to ' +os.getcwd()
    f = nwb_file.create(sessionName+'.nwb')
    
    #### generate default directories ####
    
    timeseries = f.make_group("<TimeSeries>", "timeseries", path="/acquisition/timeseries")
#    images = f.make_group('<image_X>')
#    acquisition = f.make_group('acquisition')
#    images = f.make_group('<image_X>')
#    timeseries = f.make_group('timeseries')
    
    #### generate a Session object for the desired session ####
    print '***Creating a Session object for the given session name - this may take some time.***'
    session = Session(sessionName)
    print '***Done creating a Session object.***\n'
    
    #### generate preliminary info/data ####
    
    #get raw position data
    posDict = session.make_posDict()
    #get raw LFP data
    LFP_data_list = session.load_LFPdata()
    
    #### create groups ####
    head_position = f.make_group('<module>', 'head_position')
    Position = head_position.make_group('Position', attrs= {'source': 'Data as reported in experiment files', 
                    'help': 'Position data, whether along the x, xy or xyz axis.'})
    
    #### create general groups ####
    extracellular_ephys = f.make_group('extracellular_ephys')
    extracellular_ephys.set_dataset('electrode_group', session.rec_site_group)
    extracellular_ephys.set_dataset('electrode_map', session.rec_site_map, attrs= {'units': 'meters',
            'Description': 'Depths of each recording site along each shank relative to the location of the top-most site (eg. where value = 0.0)'})
    for z in range(session.num_shanks):
        pos = extracellular_ephys.make_group('<electrode_group_X>', 'p'+str(z))
        pos.set_dataset('location', session.epos[z])
    
    
    #### write LED1 position data ####
    LED1 = Position.make_group('<SpatialSeries>', 'LED 1', attrs= {'description': 
                    'LED 1, as reported in original data. Physical position of LED (eg, left, front, etc) not known', 'source': '',
                     'comments': '', 'ancestry': 'TimeSeries,SpatialSeries', 'neurodata_type': 'TimeSeries', 'help': 
                     'Stores points in space over time. The data[] array structure is [num samples][num spatial dimenstions'})
    
    pos_data_1 = posDict[0].values()
    pos_timestamps_1 = posDict[0].keys()
    pos_num_samples_1 = len(pos_timestamps_1)
    
    LED1.set_dataset('data', pos_data_1, attrs= {'unit': 'Meters', 'conversion': '1', 'resolution': '0.001'})
            #I changed the conversion/resolution due to using CM instead of M; make sure they are correct
    LED1.set_dataset('timestamps', pos_timestamps_1, attrs= {'unit': 'Seconds', 'interval': '1'})
    LED1.set_dataset('num_samples', pos_num_samples_1)
    LED1.set_dataset('reference_frame', 'Top of room, as seen from camera')
    
    #### write LED2 position data ####
    LED2 = Position.make_group('<SpatialSeries>', 'LED 2', attrs= {'description': 
                    'LED 2, as reported in original data. Physical position of LED (eg, left, front, etc) not known', 'source': '',
                     'comments': '', 'ancestry': 'TimeSeries,SpatialSeries', 'neurodata_type': 'TimeSeries', 'help': 
                     'Stores points in space over time. The data[] array structure is [num samples][num spatial dimenstions'})
    
    pos_data_2 = posDict[1].values()
    pos_timestamps_2 = posDict[1].keys()
    pos_num_samples_2 = len(pos_timestamps_2)
    
    LED2.set_dataset('data', pos_data_2, attrs= {'unit': 'Meters', 'conversion': '1', 'resolution': '0.001'})
            #I changed the conversion/resolution due to using CM instead of M; make sure they are correct
    LED2.set_dataset('timestamps', pos_timestamps_2, attrs = {'unit': 'Seconds', 'interval': '1'})
    LED2.set_dataset('num_samples', pos_num_samples_2)
    LED2.set_dataset('reference_frame', 'Top of room, as seen from camera')
    
    #### write intermediate position data ####
    
    position = Position.make_group('<SpatialSeries>', 'position', attrs = {'description': 'Position intermediate to LED1 and LED2',
                    'source': '', 'comments': '', 'ancestry': 'TimeSeries,SpatialSeries', 'neurodata_type': 'TimeSeries', 'help': 
                     'Stores points in space over time. The data[] array structure is [num samples][num spatial dimenstions'})
    
    pos_data_real = posDict[2].values()
    pos_timestamps_real = posDict[2].keys()
    pos_num_samples_real = len(pos_timestamps_real)
    
    position.set_dataset('data', pos_data_real, attrs = {'unit': 'Meters', 'conversion': '1', 'resolution': '0.001'})
            #the exemplar files have the real position values around 10^1 or 10^2 degrees of magnitude, in meters -> I think this is an error on their part
    position.set_dataset('timestamps', pos_timestamps_real, attrs = {'unit': 'Seconds', 'interval': '1'})
    position.set_dataset('num_samples', pos_num_samples_real)
    position.set_dataset('reference_frame', 'Top of room, as seen from camera')

    #### create nwb groups/datasets for each electrode (eg. shank_0, shank_1, etc.) ####
    for x in range(session.num_shanks):
#    for x in range(2):
        name = ('shank_', str(x))
        shank = f.make_group('<module>', ''.join(name))
        
        #Clustering directory
        Clustering = shank.make_group('Clustering', attrs = {'help': 'Clustered spike data, whether from automatic \
clustering tools (eg, klustakwik) or as a result of manual sorting', 'source': 'FeatureExtraction interface, this module'})
        Clustering.set_dataset('times', session.cluster_times_list[x])
        Clustering.set_dataset('num', session.cluster_num_list[x])
        Clustering.set_dataset('description', 'Cluster #0 is electrical noise, #1 is multi-unit/unsorted, and higher numbers are unit clusters')
        ####placeholders####
        Clustering.set_dataset('peak_over_rms', [0.0,0.0,0.0])
        ####
        
        cluster_nums, times = session.get_unit_times(x)
        Clustering.set_dataset('cluster_nums', cluster_nums)
        #UnitTimes directory in Clustering
        UnitTimes = shank.make_group('UnitTimes', attrs= {'description': 'Estimated spike times from a single unit',
                                        'source': 'Clustering interface, this module.'})
        UnitTimes.set_dataset('unit_list', [str(j) for j in cluster_nums])
        for i in times.keys():
            cluster_set = UnitTimes.make_group('<unit_N>', str(i))
            cluster_set.set_dataset('times', times[i])
            cluster_set.set_dataset('source', 'From klustakwik, curated with Klusters')
            cluster_set.set_dataset('unit_description', 'unit '+str(i))      
        
        #FeatureExtraction directory
        electrode_idx = numpy.array(session.active_groups_channels[x]).reshape(-1,1)
        electrode_idx = numpy.squeeze(electrode_idx)
        FeatureExtraction = shank.make_group('FeatureExtraction', attrs = {'help': 'Container for salient features of detected events',
                        'source': 'EventWaveform interface, this module'})
        FeatureExtraction.set_dataset('features', session.feature_data_list[x])
        FeatureExtraction.set_dataset('electrode_idx', electrode_idx)
        FeatureExtraction.set_dataset('times', session.cluster_times_list[x])
        FeatureExtraction.set_dataset('description', ['PC1','PC2','PC3'])
        ######temporary, need to set this to whatever the features are per session instead of hard coding it
        
        #LFP directory
        LFP = shank.make_group('LFP', attrs = {'help': 'LFP data from one or more channels. Filter properties should be noted in the ElectricalSeries',})
        LFP_timeseries = LFP.make_group('<ElectricalSeries>', 'LFP timeseries', attrs = {'help': 'Stores acquired voltage data from extracellular recordings',
                        'source': 'Data as reported in experiment files'})
        LFP_timeseries.set_dataset('data', LFP_data_list[x], attrs = {'conversion': '1.0', 'resolution': '3.052E-7', 'units': 'Volts'})
        LFP_timeseries.set_dataset('num_samples', len(LFP_data_list[x]))
        LFP_timeseries.set_dataset('timestamps', [y/1250. for y in range(len(LFP_data_list[x]))])
        LFP_timeseries.set_dataset('electrode_idx', electrode_idx)
    #custom LFP information in /general
    LFP_info = extracellular_ephys.make_custom_group('LFP_info')
    LFP_info.set_custom_dataset('nChannels', session.LFP_meta_dict['nChannels'])         #redundant but oh well
    LFP_info.set_custom_dataset('samplingRate', session.LFP_meta_dict['samplingRate'], attrs= {'units': 'Hz'})
    LFP_info.set_custom_dataset('voltageRange', session.LFP_meta_dict['voltageRange'])
    LFP_info.set_custom_dataset('amplification', session.LFP_meta_dict['amplification'])
    LFP_info.set_custom_dataset('offset', session.LFP_meta_dict['offset'])
        
        
    f.close()
    
    print 'Finished writing .nwb file'
    session.cleanup()
    
    os.chdir(cwd)
    
def write_LFP(sessionName):
    '''
    Write a .nwb file with only LFP data.
    '''
    
    os.chdir('/media/data/Dropbox (NewmanLab)/BuzsakiData/Hippocampus/hc-3/LFP_data')
    print 'writing to ' +os.getcwd()
    f = nwb_file.create(sessionName+'.LFP_data.nwb')
    session = Session(sessionName)
    
    #get raw LFP data
    LFP_data_list = session.load_LFPdata()
    
    for x in range(len(session.cluster_times_list)):
        name = ('shank_', str(x))
        shank = f.make_group('<module>', ''.join(name))
        
        #LFP directory
        LFP = shank.make_group('LFP', attrs = {'help': 'LFP data from one or more channels. Filter properties should be noted in the ElectricalSeries',})
        LFP_timeseries = LFP.make_group('<ElectricalSeries>', 'LFP timeseries', attrs = {'help': 'Stores acquired voltage data from extracellular recordings',
                        'source': 'Data as reported in experiment files'})
        LFP_timeseries.set_dataset('data', LFP_data_list[x], attrs = {'conversion': '1.0', 'resolution': '3.052E-7', 'units': 'Volts'})
        LFP_timeseries.set_dataset('num_samples', len(LFP_data_list[x]))
        LFP_timeseries.set_dataset('timestamps', [x/1250 for x in range(len(LFP_data_list[x]))])
        
    f.close()
    
    print 'Finished writing .nwb file'
    session.cleanup()
    
    os.chdir(cwd)
    
    
def test_stuff(sessionName):
    os.chdir(target_api)
    
    print '\n\ntesting\n\n'
    
    session = Session(sessionName)
    os.chdir(session.sessionDir)
    session.load_LFPdata()
    
    session.cleanup()
    
    os.chdir(cwd)
    
    
#test_stuff('ec013.156')

write_nwb('ec012ec.356')
write_nwb('ec013.156')
write_nwb('ec013.157')
write_nwb('ec013.756')
write_nwb('ec013.965')
write_nwb('ec014.468')
write_nwb('ec014.639')
write_nwb('ec016.234')
write_nwb('ec016.749')

#write_LFP('ec012ec.356')
#write_LFP('ec013.156')
#write_LFP('ec013.157')
#write_LFP('ec013.756')
#write_LFP('ec013.965')
#write_LFP('ec014.468')
#write_LFP('ec014.639')
#write_LFP('ec016.234')
#write_LFP('ec016.749')



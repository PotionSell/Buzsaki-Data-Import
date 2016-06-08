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
#from decimal import *

os.chdir(target_api)
from nwb import nwb_file
from nwb import utils
os.chdir(cwd)


#a background function to sort lists
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
        
        #electrode position data - the positions of the session's electrodes in an array
        epos_data = numpy.genfromtxt('hc3-epos.csv', delimiter = ',', dtype = None)
#        print epos_data
        for epos in epos_data:
            if self.topGroup == str(epos[0]):
                break
        self.epos = epos
        for x in range (len(self.epos)-1, -1, -1):              #trim empty entries
            if self.epos[x] == '""':
                self.epos = numpy.delete(self.epos, x, None)
                x = x-1
        
        
        #### generate preliminary adaptation files (.csv, etc. ) needed by python from session files ####
        
        os.chdir(self.sessionDir)
        
        #change SESSIONNAME.whl position data to numpy-friendly .csv format
        f = open(self.sessionName+'.whl', 'rb')
        reader = csv.reader(f, delimiter = '\t')
        g = open(self.sessionName+'.whl.csv', 'wb')
        writer = csv.writer(g)
        writer.writerows(reader)
        f.close()
        g.close()
        
        
        #### generate raw session data from session files ####
        
        #LED position data
        self.LED_posData = numpy.genfromtxt(self.sessionName+'.whl.csv', delimiter = ',')
#        self.LED_posData = numpy.around(.01 * self.LED_posData, 15)
        self.LED_posData = self.LED_posData * 0.01
        
        #cluster timestamp data from each shank
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
        
        #cluster number data from each shank
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
            
#        arrays = tuple(arrays)
#        self.cluster_times_list = numpy.column_stack(arrays)
#        print self.cluster_times_list
            
#            array = numpy.transpose(array.reshape((-1, 1)))             #make the array 2D, then transpose it
#            print array.shape
#            self.cluster_times_list[x] = array
##            self.cluster_times_list = numpy.append(self.cluster_times_list, numpy.genfromtxt(i))
#        print self.cluster_times_list
#        print self.cluster_times_list.shape
        
#        for i in self.cluster_times_list:
#            for x in range(0, i.shape[0]):
#                i[x] = i[x] * 100
#        print self.cluster_times_list
#        for i in self.res_files:
##            print numpy.genfromtxt(i)
#            array = numpy.genfromtxt(i)
#            print array.shape
#            array = numpy.transpose(array.reshape((-1, 1)))             #make the array 2D, then transpose it
#            print array.shape
#            self.cluster_times_list = numpy.append(self.cluster_times_list, array)
#        print self.cluster_times_list
#        print self.cluster_times_list.shape

##        for i in self.cluster_times_list:
##            for x in range(0, i.shape[0]):
##                i[x] = i[x] * 100
##        print self.cluster_times_list
        
        os.chdir(cwd)
        
        
        
    ######################################################################
    #### methods to manipulate the datasets and groups of the session ####
    ######################################################################

    def make_pos_timestamps(self):
        '''
        creates a set of pos_timestamps for a given session time (times for sessions are specified in:
        /home/sidious/Desktop/docs_Bryce_s/CMB2NWBproject/NWB_sample_data/Buzsaki/Metadata/hc3-metadata-tables/hc3-session.csv
        '''

#        increment = 0.0256016385048631099332
        #The interval between recording times, a property of the Buzsaki data itself
        #Since it was not explicitly given, I calculated the average interval between each step using data from the HDF5 version:
        #   [final time value]/[inital time value] * [total # of steps]: (1013.2616487455197-8.602150537634408)/39242
        #It varies in accuracy (the lowest that I've seen has been to the 7th digit, but it can range to consistent 13th digit accuracy)
        #(I truncate the calculated timestamps to the 13th digit inclusively as that is the range of the actual timestamps)
        #(but is this level of precision even significant in context with the session context and measurement certainties?
        #this increment is constant between sessions ec013.156 and .157; I assume it is constant for all sessions
        
        
        #trying a different interval I found in the old Buzsaki-to-CMB matlab code
        increment = 1/39.06
        
        ##after successful testing, the generated timestamps can lose accuracy around the 8th decimal place (in regular notation)
        pos_timestamps = numpy.empty([int(self.sessionTime/increment)+10])  #I add 10 to ensure timestamps is longer than data
                                                                    #(so that timestamps gets trimmed in the structuredDict rather than data)
        
        for i in range(0, pos_timestamps.size):
            pos_timestamps[i] = increment *i

        #the total time ends up being a bit longer than the given time; I verified this through testing, so somehow
            #the exact lengths of the sessions given must not be quite so exact (also consider 
                #the 'blank' data at the start and end of the session which must contribute to this)
                                                
#        #trim pos_timestamps so that it doesn't include the first bit (for testing)
#        pos_timestamps = numpy.delete(pos_timestamps, numpy.s_[0:336])
        return pos_timestamps
        
        
    def make_posDict(self):
        '''
        Makes a python dictionary of the session position timestamps and position data.
        Returns three dictionaries, one corresponding to each LED, and one corresponding to calculated real position
        '''
    
        pos_timestamps = self.make_pos_timestamps()
        
        dict_1 = {}                                                         #dict for LED1 positions
        #####*************
        for i in range (    int(self.LED_posData.shape[0]   *.1)):     #here I assume that there are equal #s of x and y positions
            if self.LED_posData[i,0] >= 0 and self.LED_posData[i,.1] >= 0:         #trim out the invalid position values (-1)
                dict_1.update({pos_timestamps[i]: self.LED_posData[i,:2]})          #unsorted dict
        dict_1 = OrderedDict(sorted(dict_1.items(), key=lambda t: t[0]))    #sorted dict; could I combine these two steps?
        
        dict_2 = {}                                                         #dict for LED2 positions
        #####************************************************************
        for i in range (    int(self.LED_posData.shape[0]   *.1)):
            if self.LED_posData[i,2] >= 0 and self.LED_posData[i,3] >= 0:
                dict_2.update({pos_timestamps[i]: self.LED_posData[i,2:]})          #unsorted dict
        dict_2 = OrderedDict(sorted(dict_2.items(), key=lambda t: t[0]))    #sorted dict
        
        print '***Calculating intermediate rat position - this will take some time***'
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
        
        print '***Done calculating position***'
        return (dict_1,dict_2,dict_3)
        
        
    def get_unit_times(self, x):
        
        times = {}
#        for x in range(len(self.cluster_num_list)):
        a = self.cluster_num_list[x]
        u = numpy.unique(a)                                         #list of different cluster numbers for current shank
        indices = [numpy.argwhere(i==a) for i in numpy.unique(a)]         #list of indices of each cluster firing in the .clu data
        for y in range(len(u)):                                     #for each cluster in current shank
            shank_cluster_indices = indices[y]
            shank_times = self.cluster_times_list[x]
            t = shank_times[shank_cluster_indices]                  #find only the times that correspond to the current cluster firing
            times.update({u[y]: numpy.squeeze(t, axis=(1,))})       #numpy.squeeze changes from 2D to 1D
        return (u, times)
        
        
        
    def cleanup(self):
        '''
        Removes any files generated by the program for python compatibility.
        '''
        
        print 'Cleaning up files'
        
        os.chdir(self.sessionDir)
        
        os.remove(self.sessionName+'.whl.csv')
        
        print 'Done cleaning files'
        
        
def write_nwb(sessionName):

    #numpy.savetxt('nexttestdata', data, fmt = '%.6e', delimiter=',')   #this is the format that preserves precision
    
    ######################
    ### WRITE TO FILE ####
    ######################
    
    os.chdir(target_api)        #location to write the .nwb file to
    print 'writing to ' +os.getcwd()
    f = nwb_file.create(sessionName+'.nwb')
    
#    with nwb_file.create(sessionName+'.nwb')       #with statements don't work
    #### generate default directories ####
    
    timeseries = f.make_group("<TimeSeries>", "timeseries", path="/acquisition/timeseries")
#    images = f.make_group('<image_X>')
#    acquisition = f.make_group('acquisition')
#    images = f.make_group('<image_X>')
#    timeseries = f.make_group('timeseries')
    
    #### generate a Session object for the desired session ####
    session = Session(sessionName)
    
    ########## generate position info ##########
    
    #get raw position data
    posDict = session.make_posDict()
    
    #create .nwb groups
    head_position = f.make_group('<module>', 'head_position')
    Position = head_position.make_group('Position', attrs= {'source': 'Data as reported in experiment files', 
                    'neurodata_type': 'Interface', 'help': 'Position data, whether along the x, xy or xyz axis.'})

    
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
    LED2.set_dataset('timestamps', pos_timestamps_2, attrs= {'unit': 'Seconds', 'interval': '1'})
    LED2.set_dataset('num_samples', pos_num_samples_2)
    LED2.set_dataset('reference_frame', 'Top of room, as seen from camera')
    
    #### write intermediate position data ####
    
    position = Position.make_group('<SpatialSeries>', 'position', attrs= {'description': 'Position intermediate to LED1 and LED2',
                    'source': '', 'comments': '', 'ancestry': 'TimeSeries,SpatialSeries', 'neurodata_type': 'TimeSeries', 'help': 
                     'Stores points in space over time. The data[] array structure is [num samples][num spatial dimenstions'})
    
    pos_data_real = posDict[2].values()
    pos_timestamps_real = posDict[2].keys()
    pos_num_samples_real = len(pos_timestamps_real)
    
    position.set_dataset('data', pos_data_real, attrs= {'unit': 'Meters', 'conversion': '1', 'resolution': '0.001'})
            #the exemplar files have the real position values around 10^1 or 10^2 degrees of magnitude, in meters -> I think this is an error on their part
    position.set_dataset('timestamps', pos_timestamps_real, attrs= {'unit': 'Seconds', 'interval': '1'})
    position.set_dataset('num_samples', pos_num_samples_real)
    position.set_dataset('reference_frame', 'Top of room, as seen from camera')

    #### create nwb groups/datasets for each electrode (eg. shank_0, shank_1, etc.) ####
    for x in range(len(session.cluster_times_list)):
        name = ('shank_', str(x))
        shank = f.make_group('<module>', ''.join(name))
        clustering = shank.make_group('Clustering', attrs= {'description': 'Clustered spike data, whether from automatic \
clustering tools (eg, klustakwik) or as a result of manual sorting', 'source': 'FeatureExtraction interface, this module'})
        clustering.set_dataset('times', session.cluster_times_list[x])
        clustering.set_dataset('num', session.cluster_num_list[x])
        clustering.set_dataset('description', 'Cluster #0 is electrical noise, #1 is multi-unit/unsorted, and higher numbers are unit clusters')
        
        cluster_nums, times = session.get_unit_times(x)
        clustering.set_dataset('cluster_nums', cluster_nums)
        UnitTimes = shank.make_group('UnitTimes', attrs= {'description': 'Estimated spike times from a single unit'})
        for i in times.keys():
            cluster_set = UnitTimes.make_group('<unit_N>', str(i))
            cluster_set.set_dataset('times', times[i])
            cluster_set.set_dataset('source', 'From klustakwik, curated with Klusters')
            cluster_set.set_dataset('unit_description', 'unit '+str(i))
    
    f.close()
    
    print 'Finished writing .nwb file'
    session.cleanup()
    
    os.chdir(cwd)
    
    
def test_stuff(sessionName):
    os.chdir(target_api)
    
    print '\n\ntesting\n\n'
    
    session = Session(sessionName)
    
    
    session.cleanup()
    
    os.chdir(cwd)
    
    
#test_stuff('ec013.156')
#test_stuff('ec014.468')

write_nwb('ec013.156')
#write_nwb('ec014.639')
#write_nwb('ec013.756')
#write_nwb('750')




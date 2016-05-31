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

class Session():
    
        #create an instance of the Session class by passing a name of the desired session. This holds the session's data
    def __init__(self, sessionName):
        
        #access metadata to get session info
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
        
        
                
        #### generate session metadata from files ####
        
        #metadata: session number
        self.sessionNum = session[0]
        
        #metadata: top-level group of the session
        self.topGroup = session[1]
        
        self.sessionName = session[2]
        
        #metadata: session stimulus
        self.sessionStim = session[3]
        
        #metadata: total time
        self.sessionTime = session[5]
        
        #directory of the session
        self.sessionDir = target_data+'/'+self.topGroup+'/'+self.topGroup+'/'+self.sessionName
        
        #electrode position data - the positions of the session's electrodes in an array
        epos_data = numpy.genfromtxt('hc3-epos.csv', delimiter = ',', dtype = None)
        print epos_data
        for epos in epos_data:
            if self.topGroup == str(epos[0]):
                break
        self.epos = epos
        for x in range (len(self.epos)-1, -1, -1):
            if self.epos[x] == '""':
                self.epos = numpy.delete(self.epos, x, None)
                x = x-1
        print self.epos
        print self.epos.size
        
#        epos_data = numpy.recfromcsv('hc3-epos.csv', delimiter=',', filling_values=numpy.nan, 
#                                case_sensitive=True, deletechars='', replace_space=' ')
#        for epos in epos_data:
#            if self.topGroup == str(epos[0]):
#                break
#        self.epos = epos
#        print self.epos
#        print len(self.epos)
#        self.epos = self.epos.view((self.epos.dtype[0], len(self.epos.dtype.names)))
#        
##        for x in range (len(self.epos)-1, -1, -1):
##            if self.epos[x] == '""':
##                self.epos = numpy.delete(self.epos, x, None)
##                x = x-1
#        print self.epos
        
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
        
        
        
        
        os.chdir(cwd)
        
        
        
    ######################################################################
    #### methods to manipulate the datasets and groups of the session ####
    ######################################################################

    def make_timestamps(self):
        '''
        creates a set of timestamps for a given session time (times for sessions are specified in:
        /home/sidious/Desktop/docs_Bryce_s/CMB2NWBproject/NWB_sample_data/Buzsaki/Metadata/hc3-metadata-tables/hc3-session.csv
        '''

        increment = 0.0256016385048631099332
        #The interval between recording times, a property of the Buzsaki data itself
        #Since it was not explicitly given, I calculated the average interval between each step using data from the HDF5 version:
        #   [final time value]/[inital time value] * [total # of steps]: (1013.2616487455197-8.602150537634408)/39242
        #It varies in accuracy (the lowest that I've seen has been to the 7th digit, but it can range to consistent 13th digit accuracy)
        #(I truncate the calculated timestamps to the 13th digit inclusively as that is the range of the actual timestamps)
        #(but is this level of precision even significant in context with the session context and measurement certainties?
        #this increment is constant between sessions ec013.156 and .157; I assume it is constant for all sessions
        
        ##after successful testing, the generated timestamps can lose accuracy around the 8th decimal place (in regular notation)
        timestamps = numpy.empty([int(self.sessionTime/increment)+10])  #I add 10 to ensure timestamps is longer than data
                                                                    #(so that timestamps gets trimmed in the structuredDict rather than data)
        time = 0

        for i in range(0, timestamps.size):
            timestamps[i] = increment *i

        #the total time ends up being a bit longer than the given time; I verified this through testing, so somehow
            #the exact lengths of the sessions given must not be quite so exact (also consider 
                #the 'blank' data at the start and end of the session which must contribute to this)
                                                
#        #trim timestamps so that it doesn't include the first bit (for testing)
#        timestamps = numpy.delete(timestamps, numpy.s_[0:336])
        return timestamps
        
        
    def make_posDict(self):
        '''
        Makes a python dictionary of the session timestamps and position data.
        Returns a list of dictionaries, one corresponding to each LED, and one corresponding to calculated real position
        '''
    
        timestamps = self.make_timestamps()
        
        dict_1 = {}                                                         #dict for LED1 positions
        #####*************
        for i in range (    int(self.LED_posData.shape[0]   *.05)):     #here I assume that there are equal #s of x and y positions
            if self.LED_posData[i,0] != -1 and self.LED_posData[i,1] != -1:         #trim out the invalid position values (-1)
                dict_1.update({timestamps[i]: self.LED_posData[i,:2]})          #unsorted dict
        dict_1 = OrderedDict(sorted(dict_1.items(), key=lambda t: t[0]))    #sorted dict; could I combine these two steps?
        
        dict_2 = {}                                                         #dict for LED2 positions
        #####************************************************************
        for i in range (    int(self.LED_posData.shape[0]   *.05)):
            if self.LED_posData[i,2] != -1 and self.LED_posData[i,3] != -1:
                dict_2.update({timestamps[i]: self.LED_posData[i,2:]})          #unsorted dict
        dict_2 = OrderedDict(sorted(dict_2.items(), key=lambda t: t[0]))    #sorted dict
        
        print '***Calculating intermediate position - this will take some time***'
        dict_3 = {}
        if len(dict_1.keys()) <= len(dict_2.keys()):        #use the LED data with the fewest valid positions as reference to ensure proper position calculations
            reference_dict = dict_1
        else: reference_dict = dict_2
        for i in range (len(reference_dict.keys())):
            if timestamps[i] in dict_1.keys() and timestamps[i] in dict_2.keys():
                dict_3.update({timestamps[i]: [round((round(dict_1[timestamps[i]][0], 10) + round(dict_2[timestamps[i]][0], 10))/2, 10), round((round(dict_1[timestamps[i]][1], 10) + round(dict_2[timestamps[i]][1], 10))/2, 10)]})
        dict_3 = OrderedDict(sorted(dict_3.items(), key=lambda t: t[0]))
        
        posDict = [dict_1,dict_2,dict_3]
        return posDict
        
        
        
    def cleanup(self):
        '''
        Removes any files generated earlier for python compatibility by the Session object.
        '''
        
        os.chdir(self.sessionDir)
        
        os.remove(self.sessionName+'.whl.csv')
        
        
        
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
    session = Session(sessionName)
    
    ########## generate position info ##########
    
    #get raw position data
    posDict = session.make_posDict()
    
    #create .nwb groups
    head_position = f.make_group('<module>', 'head_position')
    Position = head_position.make_group('Position', attrs= {'source': 'Data as reported in experiment files', 
                    'neurodata_type': 'Interface', 'description': 'Position data, whether along the x, xy or xyz axis.'})

    
    #### write LED1 position data ####
    LED1 = Position.make_group('<SpatialSeries>', 'LED 1', attrs= {'description': 
                    'LED 1, as reported in original data. Physical position of LED (eg, left, front, etc) not known', 'source': '',
                     'comments': '', 'ancestry': 'TimeSeries,SpatialSeries', 'neurodata_type': 'TimeSeries', 'help': 
                     'Stores points in space over time. The data[] array structure is [num samples][num spatial dimenstions'})
    
    pos_data_1 = posDict[0].values()
    pos_timestamps_1 = posDict[0].keys()
    pos_num_samples_1 = len(pos_timestamps_1)
    
    LED1.set_dataset('data', pos_data_1, attrs= {'unit': 'Centimeters', 'conversion': '100', 'resolution': '0.1'})
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
    
    LED2.set_dataset('data', pos_data_2, attrs= {'unit': 'Centimeters', 'conversion': '100', 'resolution': '0.1'})
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
    
    position.set_dataset('data', pos_data_real, attrs= {'unit': 'Centimeters', 'conversion': '100', 'resolution': '0.1'})
            #I changed the conversion/resolution due to using CM instead of M; make sure they are correct
    position.set_dataset('timestamps', pos_timestamps_real, attrs= {'unit': 'Seconds', 'interval': '1'})
    position.set_dataset('num_samples', pos_num_samples_real)
    position.set_dataset('reference_frame', 'Top of room, as seen from camera')

    #testing:
#    pos_dict = session.make_posDict()
#    print len(pos_dict[0])
#    print OrderedDict(pos_dict[0].items()[2000:2565-301])
#    print len (pos_dict[1])
#    print OrderedDict(pos_dict[1].items()[1800:2565-301])

    
    
    
    f.close()
    
    session.cleanup()
    
    os.chdir(cwd)
    
    
write_nwb('ec013.156')
write_nwb('ec014.639')
#write_nwb('ec013.756')
#write_nwb('750')




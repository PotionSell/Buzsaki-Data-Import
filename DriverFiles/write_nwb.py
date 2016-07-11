######## write_nwb.py ########
#script that creates a Session Object and imports it and its information
#to NWB format.
#
#
##############################

#record directory that houses the program
cwd = '/media/data/Dropbox (NewmanLab)/docs (1)/docs_Bryce/CMB2NWBproject/Test_Scripts'
target_data = '/media/data/Dropbox (NewmanLab)/BuzsakiData/Hippocampus/hc-3'
target_api = '/media/data/Dropbox (NewmanLab)/docs (1)/docs_Bryce/CMB2NWBproject/api-python'         
                #this can be changed in the final implementation if I house the nwb api with the Buzsaki data
                
import os

import numpy

os.chdir(target_api)
from nwb import nwb_file
from nwb import utils
from nwb import nwb_core
os.chdir(cwd)


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
    posDict = session.get_posDict()
    #load raw LFP data
    session.load_LFPdata()
    
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
        Clustering.set_dataset('peak_over_rms', [0.0,0.0,0.0], attrs= {'placeholder': 'temporary - fix this sometime'})
        ####
        
        cluster_nums, times = session.get_UnitTimes(x)
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
        
        #omitting analysis of the .fet files for now
#        #FeatureExtraction directory
        electrode_idx = numpy.array(session.active_groups_channels[x]).reshape(-1,1)
        electrode_idx = numpy.squeeze(electrode_idx)
#        FeatureExtraction = shank.make_group('FeatureExtraction', attrs = {'help': 'Container for salient features of detected events',
#                        'source': 'EventWaveform interface, this module'})
#        FeatureExtraction.set_dataset('features', session.feature_data_list[x])
#        FeatureExtraction.set_dataset('electrode_idx', electrode_idx)
#        FeatureExtraction.set_dataset('times', session.cluster_times_list[x])
#        FeatureExtraction.set_dataset('description', ['PC1','PC2','PC3'], attrs= {'placeholder': 'temporary - fix this sometime'})
#        ######temporary, need to set this to whatever the features are per session instead of hard coding it
        
        #LFP directory
        lfp_array = dict_to_arr(session.get_shankLFP(x,True))
        LFP = shank.make_group('LFP', attrs = {'help': 'LFP data from one or more channels. Filter properties should be noted in the ElectricalSeries',})
        LFP_timeseries = LFP.make_group('<ElectricalSeries>', 'LFP timeseries', attrs = {'help': 'Stores acquired voltage data from extracellular recordings',
                        'source': 'Data as reported in experiment files'})
        LFP_timeseries.set_dataset('data', lfp_array, attrs = {'conversion': '1.0', 'resolution': '3.052E-7', 'units': 'Volts'})
        LFP_timeseries.set_dataset('num_samples', lfp_array.shape[0])
        LFP_timeseries.set_dataset('timestamps', session.LFP_timestamps)
        LFP_timeseries.set_dataset('electrode_idx', electrode_idx)
    #custom LFP information in /general
    LFP_info = extracellular_ephys.make_custom_group('LFP_info')
    LFP_info.set_custom_dataset('nChannels', session.LFP_meta_dict['nChannels'])         #redundant but oh well
    LFP_info.set_custom_dataset('spikeSamplingRate', session.LFP_meta_dict['samplingRate'], attrs = {'units': 'Hz'})
    LFP_info.set_custom_dataset('LFPsamplingRate', session.LFP_rate, attrs = {'units': 'Hz'})
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
        LFP_timeseries.set_dataset('timestamps', session.LFP_timestamps)
        
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

#write_nwb('ec012ec.356')
write_nwb('ec013.156')
#write_nwb('ec013.157')
#write_nwb('ec013.756')
#write_nwb('ec013.965')
#write_nwb('ec014.468')
#write_nwb('ec014.639')
#write_nwb('ec016.234') ######this is the problem one - some of its .fet files don't have the expected format
#write_nwb('ec016.749')


#write_LFP('ec012ec.356')
#write_LFP('ec013.156')
#write_LFP('ec013.157')
#write_LFP('ec013.756')
#write_LFP('ec013.965')
#write_LFP('ec014.468')
#write_LFP('ec014.639')
#write_LFP('ec016.234')
#write_LFP('ec016.749')





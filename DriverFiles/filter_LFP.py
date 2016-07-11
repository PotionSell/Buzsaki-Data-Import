def filter_LFP(timestamps, lfp, fs, band, graph):
    '''
    Filters lfp data from one channel (of sample rate fs) using a given frequency band. 
    Works with zero phase lag. Will graph the data and filtered data if parameter 'graph' is True.
    '''
    #This will call plot_LFP with a list of lfps, half of which are filtered
    
    #this is confirmed to be (very very very nearly) identical to the matlab implementation
    
    from scipy import signal
    import numpy as np
    import copy
    from collections import OrderedDict
    
    if band == 'theta':
        band = np.array([4.,12.])
    if band == 'delta':
        band = np.array([0.,4.])
        
    #create filter
    b,a = signal.butter(4, band*2/fs, btype = 'bandpass', analog = False)
    
    data = {}
    if graph:
        filt = copy.deepcopy(lfp)
        for i in lfp:
            filtered = signal.filtfilt(b,a,lfp[i])
            filt.update({str(i)+'*': filtered})             #make a dict with raw and filtered signals to plot
            data.update({i: filtered})
        plot_LFP(timestamps, filt, [19,20])
    else:
        for i in lfp:
            data.update({i: signal.filtfilt(b,a,lfp[i])})
#    data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))
    return data
    
#    if len(lfp.shape) > 1:          #ie. if lfp is more than 1 channel
#        if lfp.shape[1] > 1:        #ie. if lfp is more than 1 channel (I don't yet know if 1-channel lfp is of shape (#, 1) or (#,) hence the two 'if' statements
#            
###############        
#    if lfp.type is list:
#        y = []
#        
#        plt.subplot(2, len(lfp)/2, 
#        for x in range(len(lfp)):
#            i = signal.filtfilt(b,a,lfp[0])
#            y.append(i)
#            plt.subplot(2, len(lfp)/2, x+1)
#    else
#    y = signal.filtfilt(b,a,lfp)
    
    

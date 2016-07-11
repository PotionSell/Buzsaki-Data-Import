def phase_triggered_avg(phs, csd, sampleRate, phsIndex, interval):
    
    #very far from complete
    
    #assume 'phs' is in the expected format for now - scipy.signal.hilbert
    #is not yet fully working as I need so proceed without it
    
    #'phs' is phase data from the analytic signal derived through
    #hilbert analysis of filtered LFP data from one shank.
    #'phsIndex' is the user-desired phase to use in analysis
    #'interval' is the user-desired time interval to use in analysis 
    
    import numpy as np
    
    times = []
    for x in range(len(phs)):
        if phs[x] = int(phsIndex):
            times.append(x/float(sampleRate))
    timeInts = np.empty([len(times)])
    for x in range(len(times)):
        timesInts[x] = [times[x] - interval, times[x] + interval]
    
    #incomplete -- moving to matlab

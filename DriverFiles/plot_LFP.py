import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot_LFP(timestamps, lfp, interval):
    '''
    script to plot LFP data using matplotlib.pyplot
    '''
    
    if interval is 'all':
        interval = [timestamps[0], timestamps[-1]]
    
    #if the data is a dictionary, then it is LFP - plot accordingly:
    if type(lfp) is dict:
        y = []
        count = 0
        for i in lfp:
            plt.subplot(2, len(lfp)/2, count+1)
            plt.plot(timestamps, lfp[i], label='site ' +str(i))
            count = count + 1
            plt.axis([interval[0],interval[1], -0.0010, 0.0010])
            plt.xlabel('time in seconds')
            plt.ylabel('voltage in volts')
            plt.grid()
            plt.legend(loc='upper right')
    
    #if the data is a numpy array, then it is CSD - plot accordingly: (implement this)
    elif type(lfp) is numpy.ndarray:
        pass
    

    plt.show()
    
#    ####old code
#    
#    if interval is 'all':
#        interval = [timestamps[0], timestamps[-1]]
#    if type(lfp) is list:
#        for i in lfp:
#            plt.plot(timestamps, i)
#    elif type(lfp) is numpy.ndarray:
#        if len(lfp.shape) == 2:         #check to see if lfp is data from more than 1 site
#            for x in range(lfp.shape[1]):
#                plt.plot(timestamps, lfp[:, x], label='site '+str(x))
#        else:
#            plt.plot(timestamps, lfp)
#    plt.axis([interval[0],interval[1], -0.0010, 0.0010])
#    plt.xlabel('time in seconds')
#    plt.ylabel('voltage in volts')
#    plt.grid()
#    plt.legend(loc='upper right')
##    plt.savefig('test.png', bbox_inches='tight')    #to see the full legend to see what sites are invalid
#    plt.show()
    
    #<-0.002

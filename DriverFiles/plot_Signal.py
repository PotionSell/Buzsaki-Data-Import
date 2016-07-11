import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot_Signal(timestamps, signal, interval):
    '''
    Script to plot general signal data using matplotlib.pyplot.
    Distinguishes between dict (with keys pertaining to recording 
    site/channel number) and ndarray (doesn't have specific site/channel
    number labels).
    '''
    
    if interval is 'all':
        interval = [timestamps[0], timestamps[-1]]
    
    if type(signal) is dict:
        y = []
        count = 1
        for i in signal:
            plt.subplot(2, len(signal)/2, count)           #can update this to more intuitively display plots
            plt.plot(timestamps, signal[i], label='site ' +str(i))
            count = count + 1
            plt.xlim([interval[0],interval[1]])
            plt.xlabel('time in seconds')
            plt.ylabel('voltage in volts')
            plt.grid()
            plt.legend(loc='upper right')
    
    elif type(signal) is numpy.ndarray:
        if len(signal.shape) == 2:                         #check if signal contains separate datasets
            for x in range(signal.shape[1]):
                plt.plot(timestamps, signal[:, x], label='site '+str(x))
        elif len(signal.shape) == 1:
            plt.plot(timestamps, signal)
        plt.plot(timestamps, signal)
        plt.xlim([interval[0],interval[1]])
        plt.xlabel('time in seconds')
#        plt.ylabel('voltage in volts')
        plt.grid()
#        plt.legend(loc='upper right')

    plt.show()


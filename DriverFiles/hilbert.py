def hilbert(dat):
    
    #signal.hilbert doesn't produce the expected output
    
    import scipy as sp
    from scipy import signal
    import numpy as np
    
    if type(dat) is dict:
        dat = dict_to_arr(dat)
    
    hilbData = sp.signal.hilbert(dat)
    phase = np.unwrap(np.angle(hilbData))       #or not unwrap??
    amp = np.absolute(hilbData)
    
    return phase,amp, hilbData

def dict_to_arr(Dict):
    #Translates a dict (with keys that correspond to column indicies) into
    #a numpy array. 
    #***Dict does not have to be sorted but its keys must be integers***

    import numpy as np
    
    arr = np.empty([len(Dict.values()), len(Dict.keys())])
    x = 0
    for i in Dict:
        if x == 0:
            arr = Dict[i]
            arr = arr.reshape(-1,1)
        else:
            target = Dict[i]
            target = target.reshape(-1,1)
            arr = np.concatenate((arr, target), axis=1)
        x = x + 1
    return arr

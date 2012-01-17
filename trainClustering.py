
def matchTrains(oldTrains, newTrains):
    '''
    Receive two lists of trains, and match them as follows:
    
    Find the distance between each new and old train.
    Associate the two closest
    
    '''
    
    pair_distances = {}
    
    # Find the distances between all old, new trains.
    for i_old, old_train in enumerate(oldTrains):
        old_train.matched = False
        for i_new, new_train in enumerate(newTrains):
            new_train.matched = False
            pair_distances[(i_old, i_new)] = trainDistance(old_train, new_train)
    
    # Match trains from nearest to farthest:
    sorted_pairs = sorted(pair_distances, key=pair_distances.get)
    for pair in sorted_pairs:
        i_old, i_new = pair
        if oldTrains[i_old].matched == False and newTrains[i_new].matched == False\
            and pair_distances[pair] < 5: #Arbitrary threshold for now
            
            newTrains[i_new].matched = oldTrains[i_old]
            oldTrains[i_old].matched = newTrains[i_new]
    
    trainList = []
    #Check whether trains are matched, and update accordingly
    for train in newTrains:
        trainList.append(train)
        if train.matched != False:
            train.confidence += train.matched.confidence
            
    for train in oldTrains:
        if train.matched == False and train.end_of_track == False:
            train.ghost += 1
            trainList.append(train)
    return trainList

    
def trainDistance(train1, train2):
    '''
    Find the distance between two trains, in minutes.
    '''

    if train2.nextStation.seqNum < train1.nextStation.seqNum:
        train1, train2 = train2, train1
    
    next = train2.nextStation.stationCode
    t1 = train1.findETA(next)
    t2 = train2.findETA(next)
    
    t1 = float(t1)
    t2 = float(t2)
    return abs(t2 - t1)
        
        
        
    
def dictDist(dict1, dict2, drop_unmatched=False):
    '''
    Returns the distance between two dictionaries, where each key
    represents a dimension.
    
    If drop_unmatched==True, only look at distance between shared keys.
    Otherwise, treat missing keys as zero.
    '''
    
    allkeys = set(dict1.keys() + dict1.keys())
    
    dist = 0
    for key in allkeys:
        if drop_unmatched==True and key in dict1 and key in dict2:
            dist += (dict2[key] - dict1[key])**2
        else:
            dist+= (keyCheck(dict2, key) - keyCheck(dict1, key))**2
    
    return sqrt(dist)
    

def keyCheck(dict, key):
    if key in dict: 
        return dict[key]
    else:
        return 0
    
    
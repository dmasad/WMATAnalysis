'''
Created on Dec 25, 2011

@author: dmasad

A suite of functions to identify trains on a specific rail line.

'''
#from wmata import WMATA
from __future__ import division

class Train:
    '''
    Class to hold the information and methods on trains as they are identified. 
    '''
    def __init__(self, railLine):
        '''
        Create a new train, associated with a RailLine object railLine.
        '''
        self.railLine = railLine
        self.lineCode = railLine.lineCode
        self.destinationCode = railLine.endStation[0]
        self.listings = []
    
    def update_location(self, nextStation):
        '''
        The train's location is defined as the the next one it will arrive at.
        '''
        self.nextStation = nextStation
    
    def update_listings(self, newListing):
        self.listings.append(newListing)
        self.destinationCode = newListing['DestinationCode']
    
    def findETA(self, stationCode):
        for entry in self.listings:
            if entry['LocationCode'] == stationCode:
                return entry['Min']
    
    def findLocation(self):
        nextStation = self.railLine.stationDict[self.nextStation]
        if nextStation.seqNum == 0:
            # If it is the first station, assume it's at the station.
            self.lat = nextStation.lat
            self.lon = nextStation.lon
        else:
            prevStation = self.railLine.stationList[nextStation.seqNum - 1]
            nextLat = nextStation.lat
            nextLon = nextStation.lon
            prevLat = prevStation.lat
            prevLon = prevStation.lon
            
            fraction = self.findETA(self.nextStation)/nextStation.intervalTime()
            if fraction>1: 
                # Temporary hack, until better intervalTime is resolved.
                fraction = 0.1
                #print self.railLine.lineCode, self.nextStation
            self.lat = prevLat + (nextLat - prevLat)*fraction
            self.lon = prevLon + (nextLon - prevLon)*fraction
    
class Station:
    '''
    Class to store the data relating to stations on the line.
    '''
    def __init__(self, railLine, station):
        '''
        railLine: the parent RailLine object.
        station: output from the Rail Path API Method.
        '''
        self.stationCode = station['StationCode'] # The station code
        self.stationName = station['StationName']
        self.seqNum = int(station['SeqNum']) - 1 # Adjust the sequence number to correspond to the list.
        self.arrivals = [] # List of PID entry objects associated with the station
        self.intervalTimes = [] # List of estimated times from the previous station to this one.
        
        self.lat = railLine.api.getStationData(self.stationCode)['Lat']
        self.lon = railLine.api.getStationData(self.stationCode)['Lon']
        
    
    def intervalTime(self):
        '''
        Compute the current estimated travel time from the previous station.
        '''
        return sum(self.intervalTimes)/len(self.intervalTimes)
    

class RailLine:
    
    def __init__(self, API, lineCode, reverse = False):
        '''
        Create a new object storing data on a rail line in the WMATA system.
        API is an initialized WMATA API
        lineCode is a valid WMATA rail line code (RD, OR, BL, YL, GR)
        reverse determines the direction
        '''
        
        self.api = API # An instance of the WMATA API
        self.lineCode = lineCode
        self.reverse = reverse
        
        self.stationTimes = {}
        
        # List and Dictionary directories of the stations on the line.
        self.stationList = []
        self.stationDict = {}
        
        allLines = self.api.getRailLines(True) # Get data on all lines as a dict
         
        self.startStation = [allLines[self.lineCode]['StartStationCode'], allLines[self.lineCode]['InternalDestination1'] ]
        self.endStation = [allLines[self.lineCode]['EndStationCode'], allLines[self.lineCode]['InternalDestination2'] ]
        if self.lineCode == 'YL': # Temporary hard-coding to deal with error in WMATA Yellow Line coding:
            self.endStation[0] = 'E06'
            self.endStation[1] = 'B06'
        
        if self.reverse == True: # Reverse the direction if needed: 
            self.startStation, self.endStation = self.endStation, self.startStation
        
        
        path = self.api.getRailPath(self.startStation[0], self.endStation[0])
        
        for station in path:
            newStation = Station(self, station)
            self.stationList.append(newStation)
            self.stationDict[newStation.stationCode] = newStation
   
    
    def _matchPIDs(self, dictPID):
        '''
        Get the current PIDs from a dictionary of PIDs, keyed with a tuple of locationCode and endStation.
        '''
        
        for station in self.stationList:
            station.arrivals = dictPID[(station.stationCode, self.endStation)]
            # Clean up entries:
            for entry in station.arrivals:
                # Convert the arrival time to integers:
                if entry['Min'] in ['ARR', "BRD"]: 
                    entry['Min'] = 0
                else:
                    try: 
                        entry['Min'] = int(entry['Min'])
                    except:
                        continue # Ignore empty or nonstandard entries
        
    
    def findTrains(self, dictPID):
        '''
        Estimate the locations of trains in the system.
        
        dictPID: A dictionary keyed with tuples (StationCode, EndStation)
            listing all relevant PID entries for that station in that direction.
        '''
        self._matchPIDs()
        self.Trains = []

        for station in self.stationList:
            for entry in station.arrivals:
                entry['Train'] = None 
        
        startingNumber = 0
        #TODO: Handle cases where there are no trains.
        while self.stationList[startingNumber].arrivals == []:
            startingNumber = startingNumber + 1

        self.trainCount = 0
        for entry in self.stationList[startingNumber].arrivals:
            self._seekTrainForward(startingNumber, len(self.Trains))
    
    
    def _seekTrainForward(self, startingNumber, initTrainCount):
        '''
        startingNumber: Index of station to start with.
        initTrainCount: Trains already added to the system.
        
        This function works as follows:
        Start from an initial station: 
            The first available entry (one not associated with a previous train)
            becomes a new train. 
            This arrival time becomes the current maxTime
        Move to the next station:
            If the first available entry has an arrival time > maxTime:
                Associate it with the same train; this becomes new maxTime
            If there is an available entry with time < maxTime:
                Recursively launch the function forward, so that this becomes a new train.
        Continue until all stations have been traversed.
                
        '''
        
        
        trainCount = initTrainCount
        maxWait = 0 # Maximum wait time for this train.
        # Create a new train
        for entry in self.stationList[startingNumber].arrivals:
            if entry['Train'] == None:
                #Associate the entry with the new train:
                trainCount = trainCount + 1
                self.trainCount = self.trainCount + 1
                newTrain = Train(self)
                # print "Creating a new train, between " + self.path[startingNumber - 1]['StationName'] + " and " +  self.path[startingNumber]['StationName']
                newTrain.update_location(self.stationList[startingNumber].stationCode)
                entry['Train'] = trainCount
                newTrain.update_listings(entry)
                maxWait = entry['Min']
                entry['Train'] = trainCount
                break
        
        if trainCount == initTrainCount: return initTrainCount
        
        # Now advance forward:
        # TODO: replace counter with enumerate.
        counter = startingNumber + 1
        while counter < len(self.stationList):
            for entry in self.stationList[counter].arrivals:
                if entry['Train'] == None: 
                    if entry['Min'] > maxWait:
                        entry['Train'] = trainCount
                        newTrain.update_listings(entry)
                        maxWait = entry['Min']
                        break
                    else:
                        self._seekTrainForward(counter, self.trainCount)
            counter = counter + 1
        self.Trains.append(newTrain)
        
                    
    def updateStationTiming(self):
        '''
        Run only after locating trains.
        Update the estimates of the travel time from station to station based on current PID data.
        
        TODO: Make more elegant.
        This is an hacked-together temporary solution.
        Eventually, implement a full database and pull timings based on day/time.
        '''
        for index, station in enumerate(self.stationList[1:]): # Index starts counting from 0.
            for train in self.Trains:
                etaStation = train.findETA(station.stationCode)
                etaPrev = train.findETA(self.stationList[index].stationCode) # Index here = actual index - 1
                if etaStation != None and etaPrev != None:
                    timing = etaStation - etaPrev
                    station.intervalTimes.append(timing)
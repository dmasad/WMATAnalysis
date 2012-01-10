'''
Created on Jan 06, 2012

@author: dmasad

Modification of the MetroManager module to interface with a SQLite 
database for storing all the relevant information.  

'''
#import json
from collections import defaultdict
from datetime import datetime


from TrainLines import RailLine
from wmata import WMATA
from WMATADatabase import WMATADatabase

LINES = ["RD", "OR", "BL", "YL", "GR"]

class WMATAManager(object):
    '''
    A class intended to manage acquiring and analyzing data for the 
    entire Metro system. Uses a SQLite database to store the information.
    '''

    def __init__(self, api_key, database=':memory:'):
        '''
        Initialize the system with a valid WMATA API key
        '''
        self.api = WMATA(api_key)
        self.db = WMATADatabase(self, database)
        self.current_time = ""
        self.currentSchedule = [] # List that holds the current schedule.
        self.stationData = self.db.loadStations() # Dictionary that holds the station data.
        self.lineData = {}        # Dictionary that holds the API line data.
        self._getRailLines() # Load the rail line data.
        
        
        
        # Initialize the rail lines:
        # (NOTE: All necessary data should be loaded by this point)
        # ----------------------------------------------------------
        self.rail_lines = [] # List which will hold all the rail line objects.
        for line in LINES:
            for direction in [False, True]:
                self.rail_lines.append(RailLine(self, line, reverse=direction))
    
  
    
    def findTrains(self):
        '''
        Find all the trains in the current schedule.
        '''
        pidDict = self._listToDict(self.currentSchedule, ['LocationCode','DestinationCode'])
        for line in self.rail_lines:
            line.findTrains(pidDict)
     
            
    
    """
    DATA COLLECTION FROM THE API
    """
    
    def _getRailLines(self):
        #TODO: Integrate with Database
        lines_list = self.api.getRailLines()
        for line in lines_list:
            print line['LineCode']
            self.lineData[line['LineCode']] = line
    
    def getRailPath(self, startStation, endStation):
        #TODO: Integrate with Database.
        return self.api.getRailPath(startStation, endStation)
    
    def updateSchedule(self):
        '''
        Pull the updated schedule from the API.
        '''
        try:
            self.currentSchedule = self.api.updateSchedule()
            self.current_time = datetime.now()
        except:
            # TODO: Catch the error here.
            pass
  
         
    """
    JSON READ AND WRITE METHODS
    ===========================
    """
    def exportAllTracks(self, filepath):
        '''
        Generates a JSON file with the coordinates for each line.
        '''
        lineCoords = {}
        for line in self.rail_lines:
            if line.lineCode not in lineCoords:
                lineCoords[line.lineCode] = []
                for station in line.stationList:
                    newcoords = [station.stationName, station.lat, station.lon]
                    lineCoords[line.lineCode].append(newcoords)
        self.api._exportJSON(lineCoords, filepath)
    
    def exportAllTrains(self, filepath):
        '''
        Export the positions of all trains as JSON file.
        '''
        trainCoords = {}        
        for line in self.rail_lines:
            newTrains = []
            for train in line.Trains:
                train.findLocation()
                newTrains.append([train.lat, train.lon])
            if line.lineCode in trainCoords:
                trainCoords[line.lineCode] = trainCoords[line.lineCode] + newTrains
            else:
                trainCoords[line.lineCode] = newTrains
        
        self.api._exportJSON(trainCoords, filepath)
        
    """
    MISC HELPER FUNCTIONS
    ======================
    """
    
    def _listToDict(self, sourceList, keys):
        '''
        Converts sourceList, a list of Dicts, to a dict indexed by tuples of keys.
        '''
        newDict = defaultdict(list)
        for entry in sourceList:
            key = tuple(entry[dim] for dim in keys)
            newDict[key].append(entry)
        return newDict
    
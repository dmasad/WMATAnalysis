'''
Created on Dec 29, 2011

@author: dmasad
'''
import json
from TrainFinder import RailLine
from wmata import WMATA

LINES = ["RD", "OR", "BL", "YL", "GR"]

class WMATAManager:
    '''
    A class intended to manage acquiring and analyzing data for the 
    entire Metro system.
    '''

    def __init__(self, api_key):
        '''
        Initialize the system with a valid WMATA API key
        '''
        self.api = WMATA(api_key)
        
        # Initialize the rail lines:
        self.rail_lines = []
        for line in LINES:
            for direction in [True, False]:
                self.rail_lines.append(RailLine(self.api, line, reverse=direction))
    
   
    def updateLines(self):
        '''
        Gets the current PID schedule, and find all trains on all lines.
        Then update the interval timing based on the new data.
        
        UPDATED to work with the indexed dictionary.
        '''
        self.api.updateSchedule()
        scheduleDict = self.api.scheduleDict(['LocationCode','DestinationCode'])
        for line in self.rail_lines:
            line.findTrains(scheduleDict)
            line.updateStationTiming()
    
    def exportAllLines(self, filepath):
        '''
        Builds and exports a file with all station data, in JSON format.
        
        filepath: The path and name of the file to save the data to.
        '''
        for line in self.rail_lines:
            for station in line.stationList:
                if station.stationCode not in self.api.stationdata:
                    print station.stationCode
                    self.api.getStationData(station.stationCode)
        self.api.saveStationData(filepath)  
         
    def exportIntervals(self, filepath):
        '''
        Write the current interval timing between stations to a JSON file.
        
        filepath: The path and name of the file to save the data to.
        '''
        all_timings = []
        for line in self.rail_lines:
            timing = {}
            timing['Line'] = line.lineCode
            timing['reverse'] = line.reverse
            timing['timing'] = {station.stationCode : station.intervalTimes for station in line.stationList}
            all_timings.append(timing)
        
        self.api._exportJSON(all_timings, filepath)
    
    def importIntervals(self, filepath):
        '''
        Import the interval timing between stations from a JSON file.
        The JSON file must have been created with the exportSchedules()
        function above (or follow the same format).
        
        filepath: The path and name of the file to load data from.
        '''
    
        f = open(filepath, "r")
        all_intervals = json.loads(f.read())
        f.close()
        
        for line in self.rail_lines:
            for timing in all_timings:
                if timing['Line'] == line.lineCode and timing['reverse'] == line.reverse:
                    for key in timing['timing']:
                        line.stationDict[key].intervalTimes = timing['timing'][key]    
            
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
        Find the positions of all trains and export as JSON file.
        '''
        trainCoords = {}
        for line in self.rail_lines:
            newTrains = []
            line.findTrains()
            for train in line.Trains:
                train.findLocation()
                newTrains.append([train.lat, train.lon])
            if line.lineCode in trainCoords:
                trainCoords[line.lineCode] = trainCoords[line.lineCode] + newTrains
            else:
                trainCoords[line.lineCode] = newTrains
        
        self.api._exportJSON(trainCoords, filepath)

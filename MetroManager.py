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
    A class intended to manage pulling data for the entire Metro system
    '''

    def __init__(self, api_key):
        '''
        Initialize the system with a valid WMATA API key
        '''
        self.api = WMATA(api_key)
        
        self.rail_lines = []
        for line in LINES:
            for direction in [True, False]:
                self.rail_lines.append(RailLine(self.api, line, reverse=direction))
    
    def updateLines(self):
        self.api.updateSchedule()
        # Save the current schedule in order to minimize API calls.
        self.api.saveSchedule("CurrentSchedule.json")
        for line in self.rail_lines:
            line.findTrains("CurrentSchedule.json")
            line.updateStationTiming()
   
    def buildAllLines(self):
        '''
        Builds and exports a file with all station data.
        '''
        for line in self.rail_lines:
            for station in line.stationList:
                if station.stationCode not in self.api.stationdata:
                    print station.stationCode
                    self.api.getStationData(station.stationCode)
        self.api.saveStationData("StationData.json")  
         
    def exportSchedules(self, filepath):
        '''
        Write the current timing between stations to a JSON file.
        '''
        all_timings = []
        for line in self.rail_lines:
            timing = {}
            timing['Line'] = line.lineCode
            timing['reverse'] = line.reverse
            timing['timing'] = {station.stationCode : station.intervalTimes for station in line.stationList}
            all_timings.append(timing)
        
        self.api._exportJSON(all_timings, filepath)
    
    def importSchedule(self, filepath):
        f = open(filepath, "r")
        all_timings = json.loads(f.read())
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
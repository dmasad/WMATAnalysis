'''
Created on Dec 24, 2011
@author: dmasad

Python class for working with WMATA API

'''

import json
import csv
from urllib2 import urlopen


class WMATA(object):

    def __init__(self, api_key):
        self.api_key = api_key
        self.currentSchedule = [] # List that will hold the current schedule.
        self.stationdata = {}     # Dictionary that will hold station data.
    
    def getSchedule(self, stationCodes="All", saved_filepath = None):
        '''
        Returns a list of rail schedule dictionaries.
        
        stationCodes: Codes for the specific stations to look up. Generally 'All' for all stations.
        saved_filepath: Filepath to load saved schedule data, for testing and simulation purposes.
        '''
        if saved_filepath == None:
            # Update the schedule from the API and return it.
            self.updateSchedule(stationCodes)
            return self.currentSchedule
        else:
            # Load the specified saved file.
            saved_json = open(saved_filepath, "r")
            schedule_json = saved_json.read()
            saved_json.close()
            return json.loads(schedule_json)
    
    def updateSchedule(self, stationCodes="All"):
        '''
        Updates the current schedule from the API.
        '''
        url = "http://api.wmata.com/StationPrediction.svc/json/GetPrediction/" + stationCodes + "?api_key=" + self.api_key
        schedule_json = urlopen(url)
        self.currentSchedule =  json.loads(schedule_json.read())['Trains']
    
    def saveSchedule(self, filepath):
        # Save the current schedule in JSON form.
        if self.currentSchedule != []:
            f = open(filepath, "w")
            json.dump(self.currentSchedule, f)
            f.close()
        
    
    def getRailLines(self, return_dict = False):
        '''
        Return the WMATA Rail Line data
        if return_dict==False, returns as a list
        otherwise returns a Dictionary keyed by line code.
        
        First tries to load saved Rail Line data from a file.
        If that is unsuccessful, get it from the web API.
        '''
        
        try:
            lines_json = open("WMATALines.json", "r")
            lines_raw = lines_json.read()
            lines_json.close() 
        except:
            url = "http://api.wmata.com/Rail.svc/json/JLines?api_key=" + self.api_key
            lines_json = urlopen(url)
            lines_raw = lines_json.read()
            f = open("WMATALines.json", "w")
            f.write(lines_raw)
            f.close()
        lines_list = json.loads(lines_raw)['Lines']
        
        if return_dict == False: 
            return lines_list
        else:
            lines = {}
            for line in lines_list:
                lines[line['LineCode']] = line
            return lines
    
    def getRailPath(self, startStation, endStation):
        '''
        Returns a list of rail stations between startStation and endStation.
        '''
        
        url = "http://api.wmata.com/Rail.svc/json/JPath?FromStationCode=" + startStation + "&ToStationCode=" + endStation + "&api_key=" + self.api_key
        path_json = urlopen(url)
        return json.loads(path_json.read())['Path']
    
    def getStationData(self, stationCode):
        '''
        Get station data.
        '''
        if stationCode not in self.stationdata:
            url = "http://api.wmata.com/Rail.svc/json/JStationInfo?StationCode=" + stationCode + "&api_key=" + self.api_key
            station_json = urlopen(url)
            self.stationdata[stationCode] = json.loads(station_json.read())
        return self.stationdata[stationCode]
    
    def saveStationData(self, filepath):
        self._exportJSON(self.stationdata, filepath)
    
    def loadStationData(self, filepath):
        stationdata = self._importJSON(filepath)
        for station in stationdata:
            self.stationdata[station] = stationdata[station]       
    
    def export_data(self, data, filepath):
        '''
        Exports a list of dictionaries with the same fields
        to a CSV file.
        '''
        f = open(filepath, "wb")
        writer = csv.writer(f)
        row = []
        for key in data[0]:
            row.append(key)
        writer.writerow(row)
        
        for entry in data:
            row = []
            for key in entry:
                row.append(entry[key])
            writer.writerow(row)
                 
    def _writeJSON(self, json_data, filepath):
        f = open(filepath, "w")
        f.write(json_data)
        f.close()
    
    def _exportJSON(self, data, filepath):
        f = open(filepath, "w")
        json.dump(data, f)
        f.close()
        
    def _readJSON(self, filepath):
        f = open(filepath, "r")
        data = f.read()
        f.close()
        return data
    
    def _importJSON(self, filepath):
        f = open(filepath, "r")
        data = json.loads(f.read())
        return data
            
    
    def _listToDict(self, sourceList, keys):
        '''
        Converts sourceList, a list of Dicts, to a dict indexed by tuples of keys.
        '''
        newDict = {}
        for entry in sourceList:
            key = tuple(entry[dim] for dim in keys)
            if key in newDict:
                newDict[key].append(entry)
            else:
                newDict[key] = [entry]
        return newDict
                
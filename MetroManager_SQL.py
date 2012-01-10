'''
Created on Jan 06, 2012

@author: dmasad

Modification of the MetroManager module to interface with a SQLite 
database for storing all the relevant information.  

'''
#import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from time import sleep

from TrainFinder import RailLine
from wmata import WMATA

LINES = ["RD", "OR", "BL", "YL", "GR"]

class WMATAManager:
    '''
    A class intended to manage acquiring and analyzing data for the 
    entire Metro system. Uses a SQLite database to store the information.
    '''

    def __init__(self, api_key, database=':memory:'):
        '''
        Initialize the system with a valid WMATA API key
        '''
        self.api = WMATA(api_key)
        self.current_time = ""
        
        self.database = sqlite3.connect(database)
        #Check to see if the Stations table exists:
        namesResults = self.database.execute("SELECT name FROM SQLITE_MASTER").fetchall()
        names = [name[0] for name in namesResults]
        
        if "Stations" in names:
            self.loadStations()
        
        # Initialize the rail lines:
        self.rail_lines = []
        for line in LINES:
            for direction in [True, False]:
                self.rail_lines.append(RailLine(self.api, line, reverse=direction))
    
    def initializeDatabase(self):
        '''
        Initialize a new SQLite database by creating the needed tables.
        '''
        
        cursor = self.database.cursor()
        
        # Create the Stations table to store Station information.
        cursor.execute('''
            CREATE TABLE Stations
            (
            StationCode TEXT,
            Name TEXT,
            Lat REAL,
            Lon REAL,
            LineCode1 TEXT,
            LineCode2 TEXT,
            StationTogether1 TEXT
            )
        ''')
        
        
        # Create the ArrivalTimes table to store PIDs:
        cursor.execute('''
        CREATE TABLE ArrivalTimes
        (
        EntryTime TIMESTAMP,
        TrainGroup TEXT, 
        Min TEXT, 
        DestinationCode TEXT, 
        Car TEXT, 
        Destination TEXT, 
        DestinationName TEXT,
        LocationName TEXT,
        Line TEXT, 
        LocationCode TEXT
        )
        ''')
        
        # Create IntervalTimes table to store between-station interval times.
        cursor.execute('''
            CREATE TABLE IntervalTimes
            (
            EntryTime TIMESTAMP,
            LineCode TEXT,
            Direction INTEGER,
            StationCode TEXT,
            EstInterval REAL
            )
            ''')
        self.database.commit()
    
    def updateCurrentSchedule(self, saveData=False):
        '''
        Gets the current PID schedule, and find all trains on all lines.
        Then update the interval timing based on the new data.
        
        UPDATED to work with the indexed dictionary.
        '''
        cursor = self.database.cursor()
        self.api.updateSchedule()
        self.current_time = datetime.now()
        scheduleDict = self.api.scheduleDict(['LocationCode','DestinationCode'])
        for line in self.rail_lines:
            line.findTrains(scheduleDict)
        
        if saveData == True:
            for entry in self.api.currentSchedule:
                entry['CurrentTime'] = self.current_time
                cursor.execute('''
                    INSERT INTO ArrivalTimes 
                    VALUES (
                    :CurrentTime,
                    :Group,
                    :Min,
                    :DestinationCode,
                    :Car,
                    :Destination,
                    :DestinationName,
                    :LocationName,
                    :Line,
                    :LocationCode
                )''', entry)
            self.database.commit()
    
    
    def launchMonitor(self, intervalTimes, iterations, saveRate, trainFilePath):
        '''
        Launch a monitor which downloads train data and updates accordingly.
        
        intervalTimes: Seconds between iterations.
        iterations: Number of iterations.
        saveRate: Update the database once every saveRate iterations.
        trainFilePath: Filepath to export the train positions as JSON to.
        '''
        
        for i in range(iterations):
            print i
            if i % saveRate==0: saveData = True
            else: saveData = False
            
            self.importIntervals()
            self.updateCurrentSchedule(saveData)
            self.exportIntervals( )
            self.exportAllTrains(trainFilePath)
            
            #For testing purposes:
            for train in self.rail_lines[2].Trains:
                print train.nextStation, ": ", train.findETA(train.nextStation)
            
            sleep(intervalTimes)
    
    def saveStations(self):
        '''
        Updates the data on all stations in the SQL Table.
        Warning: overwrites contents of Stations table.
        '''
        # Update all stations from API
        for line in self.rail_lines:
            for station in line.stationList:
                if station.stationCode not in self.api.stationdata:
                    print station.stationCode
                    self.api.getStationData(station.stationCode)
        # Clear Stations Table:
        cursor = self.database.cursor()
        cursor.execute("DELETE FROM Stations")
        # Now write the new stations:
        cursor.executemany("INSERT INTO Stations VALUES \
                            (:Code, :Name, :Lat, :Lon, :LineCode1, :LineCode2, :StationTogether1)", 
                            [self.api.stationdata[station] for station in self.api.stationdata])
        
        self.database.commit()
     
    def loadStations(self):
        '''
        Load station data from the Stations database table.
        '''
        cursor = self.database.cursor()
        cursor.execute("SELECT * FROM Stations")
        stationResults = cursor.fetchall()
        STATIONKEYS = ["Code", "Name", "Lat", "Lon", "LineCode1", "LineCode2", "StationTogether1"]
        for stationTuple in stationResults:
            newStation = {}
            for index in range(len(STATIONKEYS)):
                newStation[STATIONKEYS[index]] = stationTuple[index]
                self.api.stationdata[newStation['Code']] = newStation
                 
         
    def exportIntervals(self):
        '''
        Write the current interval timings between stations to the database.
        '''
        
        cursor = self.database.cursor()
        for line in self.rail_lines:
            if line.reverse == False: direction = 0
            else: direction = 1
            line.updateStationIntervals()
            for station in line.stationList:
                cursor.executemany("INSERT INTO IntervalTimes VALUES  (?, ?, ?, ?, ?)", \
                                   [(self.current_time, line.lineCode, direction, station.stationCode, interval) 
                                    for interval in station.intervalTimes])
        self.database.commit()
    
    def importIntervals(self):
        '''
        Import the interval timing between stations from the database.
        At the moment, take a simple average.
        '''
        cursor = self.database.cursor()
        cursor.execute("""SELECT LineCode, Direction, StationCode, AVG(EstInterval)
                                        FROM IntervalTimes
                                        GROUP BY LineCode, Direction, StationCode
                                        """)
        intervalResults = cursor.fetchall()
        results = defaultdict(list)
        for result in intervalResults:
            if result[1]==0: reverse = False
            else: reverse = True
            results[(result[0], reverse, result[2])].append(result[3])
        for line in self.rail_lines:
            for station in line.stationList:
                station.intervalTimes = results[(line.lineCode, line.reverse, station.stationCode)]
        
         
            
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

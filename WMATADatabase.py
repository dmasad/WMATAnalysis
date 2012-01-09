'''
Created on Jan 09, 2012

@author: dmasad

Class to manage the Metro Database.
'''

import sqlite3

class WMATADatabase:
    '''
    A class intended to handle storing and retrieving Metro data from
    a SQLite database.
    '''
    
    def __init__(self, Manager, database=':memory:'):
        '''
        Create a new WMATA Database connection.
        
        Manager: the parent WMATAManager object.
        database: the database connection path.
        '''
        
        self.db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
    
    def initializeDatabase(self):
        '''
        Initialize a new SQLite database by creating the needed tables.
        '''
        
        cursor = self.db.cursor()
        
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
        self.db.commit()
        
    def saveStations(self, stationList):
        '''
        Updates the data on all stations in the SQL Table.
        Warning: overwrites contents of Stations table.
        '''
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM Stations")
        # Now write the new stations:
        cursor.executemany("INSERT INTO Stations VALUES \
                            (:Code, :Name, :Lat, :Lon, :LineCode1, :LineCode2, :StationTogether1)", 
                            stationList)
        
        self.db.commit()
     
    def loadStations(self):
        '''
        Load station data from the Stations database table.
        '''
        allStations = {}
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Stations")
        stationResults = cursor.fetchall()
        STATIONKEYS = ["Code", "Name", "Lat", "Lon", "LineCode1", "LineCode2", "StationTogether1"]
        for stationTuple in stationResults:
            newStation = {}
            for index in range(len(STATIONKEYS)):
                newStation[STATIONKEYS[index]] = stationTuple[index]
                allStations[newStation['Code']] = newStation
        return allStations
                 
         
    def saveIntervals(self, intervalList):
        '''
        Write the current interval timings between stations to the database.
        '''
        
        cursor = self.db.cursor()
        cursor.executemany("INSERT INTO IntervalTimes VALUES  (?, ?, ?, ?, ?)", \
                           [(self.current_time, line.lineCode, direction, station.stationCode, interval) 
                             for interval in station.intervalTimes])
        self.db.commit()
    
    def loadIntervals(self):
        '''
        Import the interval timing between stations from the database.
        At the moment, take a simple average.
        
        Returns a dictionary keyed by a tuple of (LineCode, Reverse)
        '''
        cursor = self.db.cursor()
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
        
    def saveSchedule(self, schedule, currentTime):
        '''
        Save a given schedule list to the database.
        '''
        cursor = self.db.cursor()
        for entry in schedule:
            entry['CurrentTime'] = currentTime
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
        self.db.commit()
    
    def loadSchedule(self, targetTime):
        '''
        Loads a schedule saved with the targetTime Timestamp.
        '''
        KEYS = ["CurrentTime", "Group", "Min", "DestinationCode", "Car", "Destination"\
                "DestinationName", "LocationName", "Line", "LocationCode"]
        allArrivals = []
        arrivalResults = self.db.execute("""SELECT * FROM ArrivalTimes 
                                        WHERE DATETIME(EntryTime) = DATETIME(?)""",\
                                        (targetTime,)).fetchall()
        for arrivalTuple in arrivalResults:
            newArrival = {}
            for index in range(len(KEYS)):
                newArrival[KEYS[index]] = arrivalTuple[index]
            allArrivals.append(newArrival)
        
        return allArrivals
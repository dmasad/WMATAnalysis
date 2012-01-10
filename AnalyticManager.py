'''
Created on Jan 9, 2012

@author: dmasad
'''

from MetroManager_SQL import WMATAManager

class AnalyticManager(WMATAManager):
    '''
    Specific implementation of WMATAManager intended to analyze existing data.
    '''
    
    def countAllTrains(self, filepath):
        '''
        Count trains across each timestamp and generate the appropriate table.
        '''
        
        cursor = self.db.db.cursor()
        cursor.execute("SELECT DISTINCT EntryTime FROM ArrivalTimes")
        timeStamps = [entry[0] for entry in cursor.fetchall()]
        
        allData = []
        for timecode in timeStamps:
            print timecode
            self.currentSchedule = self.db.loadSchedule(timecode)
            print len(self.currentSchedule)
            self.findTrains()
            for line in self.rail_lines:
                newEntry = {"TimeStamp": timecode}
                newEntry['Line'] = line.lineCode
                newEntry['Direction'] = line.reverse
                newEntry['TrainCount'] = len(line.Trains)
                allData.append(newEntry)
        self.api.export_data(allData, filepath)
                
                
                
            
            
        
        





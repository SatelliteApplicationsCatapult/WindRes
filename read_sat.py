# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 15:50:30 2015

@author: ftb14219
"""
import numpy as np
import pandas as pd
from datetime import datetime


class Sat_csv:
    
    def __init__(self, satellites, instruments, rain, winds, union):
        
        self.data=object()
        self.filepath=[]
        self.satellits=satellites
        self.inst=instruments
        self.rain=rain
        self.winds=winds
        self.union=union
        
    def read_csv(self):
        '''Reads csv file and convert it into a DataFrame'''
        if len(self.filepath)==0:
            fi=raw_input('\nSelect full, absolute path to file: ')
            self.filepath.append(fi)
        df=pd.read_csv(self.filepath[0], low_memory=False, chunksize=100000, iterator=True)
        self.data=pd.concat(df, ignore_index=True)
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Dataframe loaded >>>'
        
    def del_sentinel(self):
        '''Replace default missing values by NaN'''
        
        self.data=self.data.replace([999, -9999.0, '\N'], np.nan)
        self.data.dropna(subset=['Wspd1'], inplace=True)
        #self.data.dropna(subset=['Wdir'], inplace=True) If I do so, I will lose radiometers data since they cannot measure wind direction
        
    def filter_sat(self):
        '''Selects chosen satellites'''
        
        sats=list(self.satellits)
        if sats[0]=='All':
            pass
        else:
            self.data.set_index('Satellite', drop=False, inplace=True)
            df=self.data.ix[sats]
            self.data=df.reset_index(drop=True)

    def filter_inst(self):
        '''Selects chosen instruments'''

        instru={'Radiometers':['Radiometer'], 'Scatterometers':['Scatterometer'], 'SARs':['SAR'], 'rad-scatt':['Radiometer', 'Scatterometer'], 'scatt-SAR':['Scatterometer', 'SAR'], 'rad-SAR':['Radiometer','SAR'], 'All':'All'}
        insts=instru[self.inst]
        if insts[0]=='All':
            pass
        else:
            self.data.set_index('Instrument', drop=False, inplace=True)
            df=self.data.ix[insts]
            self.data=df.reset_index(drop=True)
    
    def convert_time(self):
        '''chnge utc time to local time according its position'''
        '''THIS METHOD IS VERY SLOW'''
        
        self.data.dropna(subset=['Time'], inplace=True)
        zone={7.5:'Etc/GMT+11', 22.5:'Etc/GMT+10', 37.5:'Etc/GMT+9', 52.5:'Etc/GMT+8', 67.5:'Etc/GMT+7', 82.5:'Etc/GMT+6', 97.5:'Etc/GMT+5', 112.5:'Etc/GMT+4', 127.5:'Etc/GMT+3', 142.5:'Etc/GMT+2', 157.5:'Etc/GMT+1', 172.5:'Etc/GMT', 187.5:'Etc/GMT-1', 202.5:'Etc/GMT-2', 217.5:'Etc/GMT-3', 232.5:'Etc/GMT-4', 247.5:'Etc/GMT-5', 262.5:'Etc/GMT-6', 277.5:'Etc/GMT-7', 292.5:'Etc/GMT-8', 307.5:'Etc/GMT-9', 322.5:'Etc/GMT-10', 337.5:'Etc/GMT-11', 352.5:'Etc/GMT-12'}
        convert=[]
        for i, row in self.data.iterrows():
            centre=((row['Long1']+row['Long2'])/2)#calculate central longitude of the square
            if centre>=352.5 or centre<7.5:
                timezone='Etc/GMT-12'
            else:
                for num in zone:
                    if num<=centre and num>(centre-15):
                        timezone=zone[num]
            res=pd.Timestamp(row['Time'])
            foo=res.tz_localize('utc')
            conv=foo.tz_convert(timezone)
            conv2=pd.to_datetime(conv)
            convert.append(conv2)
        self.data['Time']=convert
        self.data['Date']=[datetime.strptime(x, '%Y-%m-%d') for x in self.data['Date']]#it's also necessary to convert date from string format to datetime.date
        
    def filter_rain(self):
        '''Select rows with rain rate under or equal to chosen rate'''
        
        self.data['Rain'].fillna(0, inplace=True)
        self.data=self.data[self.data['Rain']<=self.rain]
        self.data=self.data.drop(['Rain'], axis=1)
        
    def filter_winds(self):
        '''Selects chosen winds'''
        
        if self.winds=='only_main':
            self.data=self.data.drop(['Wspd2', 'Wspd3'], axis=1)
            self.data['Wspd1']=np.round(self.data['Wspd1'], 2)
        else:
            self.data['Wspd1']=np.round(self.data['Wspd1'], 2)
            self.data['Wspd2']=np.round(self.data['Wspd2'], 2)
            self.data['Wspd3']=np.round(self.data['Wspd3'], 2)
            
    def indexing(self):
        '''Convert satellite or instrument columns into indexes'''
        
        if self.union=='n': 
            try:
                len(list(self.satellits))
                self.data=self.data.set_index('Satellite')
            except TypeError:
                self.data=self.data.set_index('Instrument') 
        else:
             pass          
                        
    def filtering(self):
        '''This is the execution'''        
        
        self.read_csv()
        try:
            list(self.satellits)[0]               
            if list(self.satellits)[0]!='All':
                self.del_sentinel()
                self.filter_sat()
                self.filter_rain()
                self.filter_winds()
                self.convert_time()
                self.indexing()
                print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Dataset filtered >>>'
                return self.data
                
            else:
                self.del_sentinel()
                self.filter_rain()
                self.filter_winds()
                self.convert_time()
                self.indexing()
                print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Dataset filtered >>>'
                return self.data
        except IndexError:
            if list(self.inst)[0]!='All':
                self.del_sentinel()
                self.filter_inst()
                self.filter_rain()
                self.filter_winds()
                self.convert_time()
                self.indexing()
                print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Dataset filtered >>>'
                return self.data
            else:
                self.del_sentinel()
                self.filter_rain()
                self.filter_winds()
                self.convert_time()
                print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Datasets filtered >>>'
                self.indexing()
                return self.data 


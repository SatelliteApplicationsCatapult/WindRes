# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 16:33:25 2015

@author: Alberto S. Rabaneda
"""

import sys
import os
import csv
import math
import time as tm
from datetime import datetime, timedelta
from numbers import Number
from readnc import NASAdaily as rn
import xml.etree.ElementTree as ET


class CSV_Insertion:
    ''' Inserting data from dataset to csv files'''

    def __init__(self, csvdir, rootcsv, datahub, satellite, instrument):
        
        self.csvdir=csvdir
        self.rootdir=rootcsv
        self.diccio={}
        self.world = {}
        self.hub=datahub
        if self.hub == 'rss':
            self.ilon = (0,1)
            self.ilat = (40, 41)
            self.iasc = 0
            self.missing=999
        else:
            self.ilon = ()
            self.ilat = ()
        self.satellite = satellite
        self.instrument = instrument
            
    def read_data_rss(self, filename,root):
        '''To open and read the file'''
        
        if self.satellite == 'AMSR2':
            from amsr2_daily_v7 import AMSR2daily
            dataset = AMSR2daily(filename, root, missing=self.missing)
        elif self.satellite == 'AMSRE':
            from amsr2_daily_v7 import AMSREdaily
            dataset = AMSREdaily(filename, root, missing=self.missing)
        elif self.satellite == 'Windsat':
            from windsat_daily_v7 import WindSatDaily
            dataset = WindSatDaily(filename, root, missing=self.missing)
        elif self.satellite == 'Quikscat':
            from quikscat_daily_v4 import QuikScatDaily
            dataset = QuikScatDaily(filename, root, missing=self.missing)
        elif self.satellite == 'TMI':
            from tmi_daily_v7 import TMIDaily
            dataset = TMIDaily(filename, root, missing=self.missing)
        elif self.satellite == 'ASCAT':
            from ascat_daily import ASCATDaily
            dataset = ASCATDaily(filename, root, missing=self.missing)
        elif 'SSMI' in self.satellite:
            from ssmi_daily_v7 import SSMIdaily
            dataset = SSMIdaily(filename, root, missing=self.missing)
            
            
        if not dataset.variables: 
            sys.exit('file not found')
        else:
            print filename, 'found'
            return dataset
            
    def get_files_rss(self):
        '''Iteration to read all files in a directory tree'''
        
        print 'Looping over files'
        for subdir, dirs, files in os.walk(self.rootdir):
            for item in files:
                filenom=item
                datalong=self.read_data_rss(filenom, self.rootdir)
                self.read_map_rss(datalong, filenom)
        
    def get_utmtable_rss(self):
        '''To select the correct table of the database to keep the data where each table represents a utm square'''
        
        letter={10:'c',18:'d',26:'e',34:'f',42:'g',50:'h',58:'j',66:'k',74:'l',82:'m',90:'n',98:'p',106:'q',114:'r',122:'s',130:'t',138:'u',146:'v',154:'w',162:'x'}
        if self.ilat[0]>=648:
            utmlat='x'
        else:
            for num in letter:
                if num<=(self.ilat[0]/4) and num>((self.ilat[0]/4)-8):
                    utmlat=(letter[num])      
        if int(self.ilon[0]//24)+1>30:
            utmlon=(int(self.ilon[0]//24)+1)-30
        else:
            utmlon=(int(self.ilon[0]//24)+1)+30
        table=''.join([str(utmlon), utmlat])
        return table 
                
    def read_map_rss(self, ds, filename):
        '''Iteration to read all the world map square by square'''    

        print 'Reading file:', filename
        while self.ilon[1]<=1440 and self.ilat[1]<=696:
            self.insertdict_data_rss(ds, filename)
            self.ilon=(self.ilon[0]+1,self.ilon[1]+1)
            if self.ilon[1]==1441:
                self.ilon=(0,1)
                self.ilat=(self.ilat[0]+1,self.ilat[1]+1)
                if self.ilon[1]==1 and self.ilat[1]==697 and self.iasc==0:
                    self.iasc=1
                    self.ilat=(40,41)
                elif self.ilon[1]==1 and self.ilat[1]==697 and self.iasc==1:
                    self.ilat=(40,41)
                    self.asc=0
                    self.insert_csv(filename)
                    print filename, 'transformed into csv succesfully'
                    self.world.clear()
                    break
                
    def insertdict_data_rss(self, ds, filename):
        '''Read and insert data into world dictionary'''

        wind_dict={'AMSR2':('windLF', 'windMF'), 'AMSRE':('windLF', 'windMF'), 'TMI':('w11', 'w37'), 'ASCAT':('windspd'), 'Quikscat':('windspd'), 'Windsat':('w-aw', 'w-lf', 'w-mf'), 'SSMIf08':('wind'), 'SSMIf08':('wind'), 'SSMIf10':('wind'), 'SSMIf11':('wind'), 'SSMIf13':('wind')}
        wspd1=float(ds.variables[wind_dict[self.satellite][0]][self.iasc, self.ilat[0]:self.ilat[1],self.ilon[0]:self.ilon[1]])
        try:
            wspd2=float(ds.variables[wind_dict[self.satellite][1]][self.iasc, self.ilat[0]:self.ilat[1],self.ilon[0]:self.ilon[1]])
        except IndexError:
            wspd2 = None
        try:
            wspd3=float(ds.variables[wind_dict[self.satellite][2]][self.iasc, self.ilat[0]:self.ilat[1],self.ilon[0]:self.ilon[1]])
        except IndexError:
            wspd3 = None
        if wspd1==999 and wspd2==999:
            pass
        else:
            sat=self.satellite
            inst=self.instrument
            # here filename [:] is gonna be different for each satellite 
            if 'SSMI' or 'AMSR2' or 'TMI' in self.satellite:
                nom=filename[4:12]
            elif 'Quik' or 'ASCAT' or 'AMSRE' in self.satellite:
                nom = filename[6:14]
            elif 'Wind' in self.satellite:
                nom = filename[5:13]
            date= datetime.strptime(nom, '%Y%m%d')
            if self.ilon[0]<720:
                longi1=(self.ilon[0]*0.25)+180
                longi2=(self.ilon[1]*0.25)+180
            else:
                longi1=(self.ilon[0]*0.25)-180
                longi2=(self.ilon[1]*0.25)-180
            lati1=self.ilat[0]*0.25
            lati2=self.ilat[1]*0.25
            if 'TMI' or 'AMSR' or 'SSMI' in self.satellite:
                hours=float(ds.variables['time'][self.iasc, self.ilat[0]:self.ilat[1], self.ilon[0]:self.ilon[1]])
                time=tm.strftime('%H:%M:%S', tm.gmtime(hours*3600))
            elif 'ASCAT' or 'Quik' or 'Wind' in self.satellite:
                minutes=float(ds.variables['mingmt'][self.iasc, self.ilat[0]:self.ilat[1], self.ilon[0]:self.ilon[1]])
                time=tm.strftime('%H:%M:%S', tm.gmtime(minutes*60))
            try:
                drops=float(ds.variables['rain'][self.iasc, self.ilat[0]:self.ilat[1], self.ilon[0]:self.ilon[1]])
            except KeyError:
                drops=float(ds.variables['radrain'][self.iasc, self.ilat[0]:self.ilat[1], self.ilon[0]:self.ilon[1]])
            if 'ASCAT' or 'Quik' in self.satellite:
                wdir1=float(ds.variables['winddir'][self.iasc, self.ilat[0]:self.ilat[1], self.ilon[0]:self.ilon[1]])
            elif self.satellite == 'Windsat':
                wdir1=float(ds.variables['wdir'][self.iasc, self.ilat[0]:self.ilat[1], self.ilon[0]:self.ilon[1]])
            else:
                wdir1 = None
            if wspd1==999:
                wspd1=None
            if wspd2==999:
                wspd2=None
            if drops==999:
                drops=None
            mydata=(sat, inst, longi1, longi2, lati1, lati2, date, time, wspd1, wspd2, wspd3, wdir1, drops)
            utmtable=self.get_utmtable_rss()
            if not utmtable in self.world:
                self.world[utmtable]=[mydata]
            else:
                self.world[utmtable].append(mydata)
                
    def get_utmtable(self):
        '''To select the correct table of the database to keep the data where each table represents a utm square'''
        
        letter={10:'c',18:'d',26:'e',34:'f',42:'g',50:'h',58:'j',66:'k',74:'l',82:'m',90:'n',98:'p',106:'q',114:'r',122:'s',130:'t',138:'u',146:'v',154:'w',162:'x'}
        if (self.ilat[0])>=162:
            utmlat='x'
        else:
            for num in letter:
                if num<=(self.ilat[0]) and num>((self.ilat[0])-8):
                    utmlat=(letter[num]) 
        utmlon=(int(self.ilon[0]//6)+1)
        table=''.join([str(utmlon), utmlat])
        return table   
        
    def get_files_nasa(self):
        '''Iteration to read all files in a directory tree'''
        
        print 'Looping over files'
        for subdir, dirs, files in os.walk(self.rootdir):
            for item in files:
                filenom=item
                nasa=rn(filenom, self.rootdir)
                datalong=rn.read_nc(nasa)
                self.read_map_nasa(datalong, filenom, self.rootdir)
                
    def insertdict_data_nasa(self, sec, lt, lt1, lt0, ln, ln1, ln0, ws, ws2, ws3, wd, dr):
        '''Read and insert data into world dictionary'''
        
        self.ilat=(((lt+lt0)/2),((lt+lt1)/2))    
        if self.ilat[0]<10 or self.ilat[0]>=174 or isinstance(ws, Number)==False or ws==-9999.0:
            pass
        else:
            sat=self.satellite
            inst=self.instrument
            moment=datetime(1999,1,1,0,0,0)+timedelta(seconds=sec)
            date=moment.date()
            time=moment.time()
            # average of two angles
            radln0=math.radians(ln0)
            radln=math.radians(ln)
            radln1=math.radians(ln1)
            pri=math.degrees(math.atan((math.sin(radln0)+math.sin(radln))/(math.cos(radln0)+math.cos(radln))))+180
            segu=math.degrees(math.atan((math.sin(radln1)+math.sin(radln))/(math.cos(radln1)+math.cos(radln))))+180
            self.ilon=(pri, segu)
            if dr==-9999.0:
                dr=None
            mydata=(sat, inst, self.ilon[0], self.ilon[1], self.ilat[0], self.ilat[1], date, time, ws, ws2, ws3, wd, dr)
            utmtable=self.get_utmtable()
            if not utmtable in self.world:
                self.world[utmtable]=[mydata]
            else:
                self.world[utmtable].append(mydata)
                
    def read_map_nasa(self, ds, filename, root):
        '''Iteration to read all the world map square by square''' 

        nasa=rn(filename, root)
        [varis, var_attr_list, var_data_list] = rn.readVars(nasa,ds)
        try:
            print 'Reading file:', filename
            for j in range(0,3248):
                secs=int(var_data_list[0][j])
                # Due to squares are not exavtly equal size, it is necessary to calculate the four coordinates calculating the medium value
                if var_data_list[2][j][0]<var_data_list[2][j][151]:
                    for i in range(0,152):
                        lat=float("{0:.4f}".format(var_data_list[1][j][i]))+90
                        if i==151:
                            #0.125 because resolution is 12.5 km
                            lat1=(lat+0.125)
                        else:
                            lat1=float("{0:.4f}".format(var_data_list[1][j][i+1]))+90
                        if i==0:
                            lat0=(lat-0.125)
                        else:
                            lat0=float("{0:.4f}".format(var_data_list[1][j][i-1]))+90
                        lon=float("{0:.4f}".format(var_data_list[2][j][i]))
                        if i==151:
                            lon1=lon+0.125
                            if lon1>360:
                                lon1=(lon+0.125)-360
                        else:
                            lon1=float("{0:.4f}".format(var_data_list[2][j][i+1]))
                        if i==0:
                            lon0=lon-0.125
                            if lon0<0:
                                lon0=(lon-0.125)+360
                        else:
                            lon0=float("{0:.4f}".format(var_data_list[2][j][i-1]))
                        wspd=var_data_list[3][j][i]
                        wspd2=var_data_list[8][j][i]
                        wspd3=var_data_list[10][j][i]
                        wdir=var_data_list[4][j][i]
                        drops=var_data_list[5][j][i]
                        self.insertdict_data_nasa(secs, lat, lat1, lat0, lon, lon1, lon0, wspd, wspd2, wspd3, wdir, drops)
                else:
                    for i in range(151,-1,-1):
                        lat=float("{0:.4f}".format(var_data_list[1][j][i]))+90
                        if i==151:
                            lat1=(lat+0.125)
                        else:
                            lat1=float("{0:.4f}".format(var_data_list[1][j][i+1]))+90
                        if i==0:
                            lat0=(lat-0.125)
                        else:
                            lat0=float("{0:.4f}".format(var_data_list[1][j][i-1]))+90
                        lon=float("{0:.4f}".format(var_data_list[2][j][i]))
                        if i==151:
                            lon0=lon-0.125
                            if lon0<0:
                                lon0=(lon-0.125)+360
                        else:
                            lon0=float("{0:.4f}".format(var_data_list[2][j][i+1]))
                        if i==0:
                            lon1=lon+0.125
                            if lon0>360:
                                lon0=(lon+0.125)-360
                        else:
                            lon1=float("{0:.4f}".format(var_data_list[2][j][i-1]))
                        wspd=var_data_list[3][j][i]
                        wspd2=var_data_list[8][j][i]
                        wspd3=var_data_list[10][j][i]
                        wdir=var_data_list[4][j][i]
                        drops=var_data_list[5][j][i]
                        self.insertdict_data_nasa(secs, lat, lat1, lat0, lon, lon1, lon0, wspd, wspd2, wspd3, wdir, drops)
        finally:
            rn.closing(nasa, ds)
        self.insert_csv(filename)
        print filename, 'transformed into csv succesfully'
        self.world.clear()
        
    def get_files_s1tbx(self):
        '''Iteration to read all files in a directory tree'''
        
        print 'Looping over files'
        resolution = input('Resolution of SAR data in km x km: ') 
        for subdir, dirs, files in os.walk(self.rootdir):
            for item in files:
                filenom=item
            self.read_map_s1tbx(filenom, resolution)
            
    def read_map_s1tbx(self, filename, resolution):
        '''Iteration to read all the world map square by square''' 

        print 'Reading file:', filename
        filepath=''.join([self.rootdir, '/', filename])
        tree = ET.parse(filepath)
        root = tree.getroot()
        for info in root.iter('windFieldInfo'):
            date= datetime.strptime(filename[17:25], '%Y%m%d')
            time=datetime.strptime(filename[26:32], '%H%M%S')
            wspd=float(info.attrib['speed'])
            wdir=float(info.attrib['dx']) + float(info.attrib['dy'])
            lat=(float(info.attrib['lat']))+90
            lon=(float(info.attrib['lon']))+180
            border=resolution/100
            self.ilon=((lon-border),(lon+border))
            self.ilat=((lat-border),(lat+border))
            self.insertdict_data_s1tbx(date, time, self.ilon[0], self.ilon[1], self.ilat[0], self.ilat[1], wspd, wdir)
        self.insert_csv(filename)
        print filename, 'transformed into csv succesfully'
        self.world.clear()
        
    def insertdict_data_s1tbx(self, dt, tm, ln0, ln1, lt0, lt1, ws, wd):
        '''Read and insert data into world dictionary'''

        wspd1=ws    
        if lt0<10 or lt0>=174 or isinstance(wspd1, Number)==False:
            pass
        else:
            sat=self.satellite
            inst=self.instrument
            wspd2=None
            wspd3=None
            mydata=(sat, inst, ln0, ln1, lt0, lt1, dt, tm, ws, wspd2, wspd3, wd)
            utmtable=self.get_utmtable()
            if not utmtable in self.world:
                self.world[utmtable]=[mydata]
            else:
                self.world[utmtable].append(mydata)

        
    def insert_csv(self):
        '''To insert the dictionary world in the different csv files before inseting them into database'''
        
        print 'Keeping ', self.filename, 'into csv tables'
        for var in self.diccio:
            csvname=''.join([var,'.csv'])
            filepath=os.path.join(self.csvdir, csvname)
            with open(filepath, "ab") as myfile:
                wr=csv.writer(myfile)
                for row in self.diccio[var]:
                    wr.writerow(row)
                myfile.close()
    

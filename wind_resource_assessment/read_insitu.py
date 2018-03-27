# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 12:07:21 2015

@author: Alberto S. Rabaneda
"""

import pandas as pd
import numpy as np
import datetime
from pandas import DataFrame
import dateutil.parser as parser
from scipy import special
from sat_processing import Merging
from scipy.spatial import KDTree
import sys
import re
from dateutil.parser import parse
import Commons
import warnings
import math

class Read_excel:
    
    def __init__(self, coordinates, excel, satellites, term='long', neutral=False):
        
        self.heights=[]
        self.dataframe=DataFrame()
        self.cordis=[]
        self.sats=satellites
        self.coord=coordinates
        self.file=excel
        self.term=term
        self.neutral=neutral
                
    def select_cordis(self):
        
        print '\nCoordinates of acquisition for file '+self.file+':'
        lon=input('\tLongitude (-180 to 180):')
        lat=input('\tLatitude (-90 to 90):')
        self.cordis.append(lon)
        self.cordis.append(lat)
    
    def select_heights(self):
        
        print '\nSelect heights to calculate parameters for file '+self.file+':'
        h1=input('\tLowest height:')
        h2=input('\tHighest height:')
        self.heights.append(h1)
        self.heights.append(h2)
        hub=input('\tSelect hub height:')
        self.heights.append(hub)
        
    def open_excel(self, filepath):
        
        table=pd.read_excel(filepath, sheetname='Data', converters={'DATE&TIME STAMP':str, 'DAY':str, 'TIME':str})        
        #xlsx_file=pd.ExcelFile(filepath)
        #table=xlsx_file.parse('Data')
        try:
            table.replace('\N', np.nan, inplace=True)
        except UnboundLocalError:
            pass
        return table
        
    def del_sentinel(self, data):
        '''Replace default missing values by NaN'''
        
        print '\nWhat is the default missing value/s (e.g. -999): '
        defaults=[]
        s=0
        for i in range(10):
            s+=1
            default=raw_input('\tValue '+str(s)+': ')
            if default=='':
                break
            else:
                defaults.append(default)
                continue
        try:
            datis=data.replace(defaults, np.nan)
        except AttributeError:
            datis=data
        return datis
        
    def remove_negatives(self, data):
        '''This method removes negatives wind directions and speeds, not only that value but the entire row'''
        
        dati=data.fillna(0)
        direcs=[x for x in list(data.columns) if 'DIREC' in x ]
        for item in direcs:
            datas=dati[dati[item]>=0]
        speedies=[x for x in list(data.columns) if 'SPEED' in x ]
        for item in speedies:
            datas=dati[dati[item]>=0]
        return datas
    
    def neutral_stability(self, frame, Tdif=1):
        '''Filter for neutral conditions,Tsea equal Tair. It is assumed a difference of 3 degrees as maximum'''        
        
        listin=[]
        for i, row in frame.iterrows():
            value=abs(row['TEMPERATURE(C)']-row['TSEA(C)'])
            if value<=Tdif and value!=np.nan:
                listin.append(row)
            else:
                continue
        print 'Measurements under neutral conditions = '+str(len(listin))
        data=pd.concat(listin, axis=1, ignore_index=True)
        df=data.T
        return df
        
    def stability_correction(self, frame):
            '''Calculation of stability correction for the low and high heights selected'''
           
            h1=self.heights[0]
            h2=self.heights[1]
            name1='VIRTUAL TEMP(K)'+str(h1)
            name2='VIRTUAL TEMP(K)'+str(h2)
            for col in frame.columns:
                if str(h1) in col:
                    if 'TEMPER' in col:
                        T1=col
                    elif 'PRESS' in col:
                        P1=col
                    elif 'HUMI' in col:
                        H1=col
                    elif 'VERTI' in col:
                        V1=col
                    else:
                        continue
                elif str(h2) in col:
                    if 'TEMPER' in col:
                        T2=col
                    elif 'PRESS' in col:
                        P2=col
                    elif 'HUMI' in col:
                        H2=col
                    elif 'VERTI' in col:
                        V2=col
                    else:
                        continue
            #(1+0.61*mixing ratio)*temperature*((1000/pressure)**(287.058*(1-0.23*humidity)/1005))
            frame.loc[:,'pw'+str(h1)]=(((np.e**(77.3450+0.0057*(frame[T1]+273.15)-7235/(frame[T1]+273.15)))/(frame[T1]+273.15)**8.2)/100)*frame[H1]/100
            frame.loc[:,'pw'+str(h2)]=(((np.e**(77.3450+0.0057*(frame[T2]+273.15)-7235/(frame[T2]+273.15)))/(frame[T2]+273.15)**8.2)/100)*frame[H2]/100
            frame.loc[:, name1]=(1+0.61*(621.9907*frame['pw'+str(h1)]/(frame[P1]-frame['pw'+str(h1)])))*(frame[T1]+273.15)*((1000/frame[P1])**(0.286))
            frame.loc[:, name2]=(1+0.61*(621.9907*frame['pw'+str(h2)]/(frame[P2]-frame['pw'+str(h2)])))*(frame[T2]+273.15)*((1000/frame[P2])**(0.286))
            
            frame.set_index('Date', inplace=True, drop=False)
            frame.sort_index(inplace=True)
            times=[-20,-10,0,10,20]
            heatflux1=[]
            heatflux2=[]
            for z, row in frame.iterrows():
                vertical1=[]
                vertical2=[]
                virtual1=[]
                virtual2=[]
                for i in times:
                    try:
                        time=row['Date']+datetime.timedelta(minutes=i)
                        vel=frame.ix[time][V1]
                        vertical1.append(vel)
                        vel2=frame.ix[time][V2]
                        vertical2.append(vel2)
                        virt1=frame.ix[time][name1]
                        virtual1.append(virt1)
                        virt2=frame.ix[time][name2]
                        virtual2.append(virt2)
                    except KeyError:
                        continue
                    
                if len(vertical1)<=1:
                    heat1=np.nan
                    heat2=np.nan
                else:
                    heat1=(row[V1]-np.average(vertical1))*(row[name1]-np.average(virtual1))
                    heat2=(row[V2]-np.average(vertical2))*(row[name2]-np.average(virtual2))
                
                heatflux1.append(heat1)
                heatflux2.append(heat2)   
            frame.loc[:, 'heatflux'+str(h1)]=heatflux1
            frame.loc[:, 'heatflux'+str(h2)]=heatflux2
            
            stability1=[]
            stability2=[]
            length1=[]
            length2=[]
            meanhf1=[]
            meanhf2=[]
            listx1=[]
            listx2=[]
            a=0
            for z, row in frame.iterrows():
                vtemperature1=[]
                vtemperature2=[]
                heatf1=[]
                heatf2=[]
                for i in times:
                    try:
                        time=row['Date']+datetime.timedelta(minutes=i)
                        hf1=frame.ix[time]['heatflux'+str(h1)]
                        heatf1.append(hf1)
                        hf2=frame.ix[time]['heatflux'+str(h2)]
                        heatf2.append(hf2)
                        tt1=frame.ix[time][name1]
                        vtemperature1.append(tt1)
                        tt2=frame.ix[time][name2]
                        vtemperature2.append(tt2)
                    except KeyError:
                        continue
                if len(heatf1)<=1:
                    a+=1
                    stb1=np.nan
                    stb2=np.nan
                    L1=np.nan
                    L2=np.nan
                    mhf1=np.nan
                    mhf2=np.nan
                    x1=np.nan
                    x2=np.nan
                else:
                    mhf1=np.average(heatf1)
                    mhf2=np.average(heatf2)
                    L1=((-1)*(np.average(vtemperature1))*row['u*']**3)/(0.4*9.81*(mhf1))
                    L2=((-1)*(np.average(vtemperature2))*row['u*']**3)/(0.4*9.81*(mhf2))
                    if mhf1>-0.001 and mhf1<0.001:
                        stb1=0
                        x1=np.nan
                    elif mhf1>0:
                        xx1=(1-12*h1/L1)
                        x1=xx1**(1./3)
                        stb1=((3./2)*np.log((1+x1+(x1**2))/3.))-((3**(1./2))*math.atan((1+2*x1)/(3**(1./2))))+(np.pi/3**(1./2))
                    elif mhf1<0:
                        stb1=-4.7*float(h1)/L1
                        x1=np.nan
                    if mhf2>-0.001 and mhf2<0.001:
                        stb2=0
                        x2=np.nan
                    elif mhf2>0:
                        xx2=(1-12*h2/L2)
                        x2=xx2**(1./3)
                        stb2=((3./2)*np.log((1+x2+(x2**2))/3.))-((3**(1./2))*math.atan((1+2*x2)/(3**(1./2))))+(np.pi/3**(1./2))
                    elif mhf2<0:
                        stb2=-4.7*float(h2)/L2
                        x2=np.nan           
                length1.append(L1)
                length2.append(L2)
                stability1.append(stb1)
                stability2.append(stb2)
                meanhf1.append(mhf1)
                meanhf2.append(mhf2)
                listx1.append(x1)
                listx2.append(x2)
                
                
            print 'Not enough correlative data: '+str(a)+' times'
            frame.loc[:, 'MOlength'+str(h1)]=length1
            frame.loc[:, 'MOlength'+str(h2)]=length2
            frame.loc[:, 'stability'+str(h1)]=stability1
            frame.loc[:, 'stability'+str(h2)]=stability2
            frame.loc[:, 'mean_hfx'+str(h1)]=meanhf1
            frame.loc[:, 'mean_hfx'+str(h2)]=meanhf2
            frame.loc[:, 'x'+str(h1)]=listx1
            frame.loc[:, 'x'+str(h2)]=listx2
            
            for tru in list(frame.columns):
                check=re.findall(r'\d+', tru)
                if str(self.heights[0]) in check and 'SPEED' in tru:
                    spd1=tru
                else:
                    continue           
            frame.loc[:, 'z0_stability']=float(h1)/(np.e**((frame[spd1]*0.4/frame['u*'])+(frame['stability'+str(h1)])))   
            return frame

    def preparing(self):        

        fra=self.open_excel(self.file)
        framing=self.del_sentinel(fra)
        if self.neutral==True:
            frame=self.neutral_stability(framing)
        else:
            frame=framing
        col=list(frame.columns)
        if 'DATE&TIME STAMP' in col:
            try:
                frame['Date']=[datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')for x in frame['DATE&TIME STAMP']]         
            except TypeError:
                pass
                #frame['Date']=[x for x in frame['DATE&TIME STAMP']]
                #frame['Time']=[x for x in frame['DATE&TIME STAMP']]
            except ValueError:
                frame['Date']=[parse(x) for x in frame['DATE&TIME STAMP']]
            frame['Time']=frame['Date']
            a=frame.drop('DATE&TIME STAMP', axis=1)
        else:
            try:
                frame['Date']=[datetime.datetime.strptime(x, '%Y-%m-%d') for x in frame['DAY']]
                frame['Time']=[datetime.datetime.strptime(x, '%H:%M:%S') for x in frame['TIME']]
            except TypeError:
                pass
                #frame['Date']=[x.date() for x in frame['DAY']]
                #frame['Time']=[x.time() for x in frame['TIME']]
            except ValueError:
                frame['Date']=[parse(x) for x in frame['DAY']] #this is wrong, join date and time in Date column
                frame['Time']=[parse(x) for x in frame['TIME']]
            a=frame
        a['Device']=self.file
        fr1=self.calculs(a)
        fr2=self.drag(fr1)
        fr3=self.insitu_friction(fr2)
        trues=self.friction(fr3)
        if self.neutral==False:
            #fr35=self.stability_correction(trues)
            fr35=trues
        else:
            fr35=trues
        sp0=self.gust(fr35)
        #sp1=self.beta(sp0)
        sp2=self.phase_speed(sp0)
        sp25=self.wave_age(sp2)
        sp3=self.relative_speed(sp25)
        sp4=self.drag_insitu(sp3)
        sp41=self.wind10(sp4)
        sp45=self.k_viscosity(sp41)
        
        
        tru=self.remove_negatives(sp45)
        if self.sats!=None:
            plas=self.select_cell(tru)
        else:
            resolution=raw_input('Choose resolution of grid (0.02, 0.16, 0.25 or None): ')
            if resolution=='0.16':
                self.sats=['Rapidscat']
            elif resolution=='0.25':
                self.sats=['Windsat']
            else:
                self.sats=['All']
            plas=self.select_cell(tru)
        self.dataframe=self.set_clock(plas)
        
    def set_clock(self, dataframe):
        '''Creates a new column to set when it's day or night, it's not considered seasonal variations,
        for in-situ measurements it is assumed that time is in local time'''
        
        daylist=[]
        morning=datetime.time(7,0,0)
        evening=datetime.time(19,0,0)
        a=0
        for i, row in dataframe.iterrows():
            clock=row['Time']
            try:
                if clock.time()>=morning and clock.time()<evening:
                    daylist.append('day')
                else:
                    daylist.append('night')
            except TypeError:
                a+=1
                daylist.append(np.nan)
        days=pd.Series(daylist)
        dataframe.loc[:, 'Day/Night']=days
        print str(a)+' time errors'
        return dataframe

    def avg_roughness(self, frame, h1, h2, spd1, spd2):
        '''frame must have a timestamp index and Date column, which is the same than index'''
        
        times=[-20,-10,0,10,20]
        for z, row in frame.iterrows():
                vel1=[]
                vel2=[]
                for i in times:
                    try:
                        time=row['Date']+datetime.timedelta(minutes=i)
                        vel1.append(frame.ix[time][spd1])
                        vel2.append(frame.ix[time][spd2])
                    except KeyError:
                        continue
                rough=np.e**(((np.average(vel1)*np.log(h2))-(np.average(vel2)*np.log(h1)))/(np.average(vel1)-np.average(vel2)))              
                yield rough
         
    def calculs(self, df, max_z=2):
        '''Here it's used the log law for neutral conditions, that is the assumption. I should use log law with stability correction only'''
        
        h1=self.heights[0]
        h2=self.heights[1]
        hubh=self.heights[-1]
        for tru in list(df.columns):
            check=re.findall(r'\d+', tru)
            if str(h1) in check and 'SPEED' in tru:
                spd1=tru
            elif str(h2) in check and 'SPEED' in tru:
                spd2=tru
            else:
                continue
        
        df.dropna(subset=[spd1, spd2], inplace=True)
        df[[spd1, spd2]]=df[[spd1,spd2]].astype(float)
        df.set_index('Date', inplace=True, drop=False)
        df.sort_index(inplace=True)
        
                
        
        if h2!=hubh:
            if self.term=='instant':
                g=self.avg_roughness(df, h1, h2, spd1, spd2)
                df['Roughness']=list(g)
                df['Wlifted1']=df[spd2]*((np.log(hubh/df['Roughness']))/(np.log(h2/df['Roughness'])))
            else:
                df['Roughness']=np.e**(((np.average(df[spd1])*np.log(h2))-(np.average(df[spd2])*np.log(h1)))/(np.average(df[spd1])-np.average(df[spd2])))
                df['Wlifted1']=(np.average(df[spd2])*(np.log(hubh/np.average(df['Roughness']))))/(np.log(h2/np.average(df['Roughness'])))
                df['Wspd1']=df[spd2]
        elif h2==hubh:
            if self.term=='instant':
                g=self.avg_roughness(df, h1, h2, spd1, spd2)
                df['Roughness']=list(g)
                df['Wlifted1']=df[spd2]
            else:
                df['Roughness']=np.e**(((np.average(df[spd1])*np.log(h2))-(np.average(df[spd2])*np.log(h1)))/(np.average(df[spd1])-np.average(df[spd2])))
                df['Wlifted1']=df[spd2]
                df['Wspd1']=df[spd2]
        dif=df[df['Roughness']<2]
        return dif
        
    def wind10(self, frame):
        
        frame.loc[:, 'U10']=(np.log(10/frame['Roughness']))*(frame['insitu_friction']/0.4)
        return frame
     
    def drag(self, frame):
        
        if self.term=='long':
            frame.loc[:, 'Cd']=((0.4/(np.log(self.heights[0]/np.average(frame['Roughness']))))**2)*1000            
        elif self.term=='instant':
            frame.loc[:, 'Cd']=((0.4/(np.log(self.heights[0]/(frame['Roughness']+0.0000001))))**2)*1000
        return frame
        
    def beta(self, frame):
        
        if self.neutral==True:
            frame.loc[:,'beta']=(frame['Roughness']*frame['Gustiness']**2)/((0.4/np.log(10/frame['Roughness']))**2)
            print 'done'
        elif self.neutral==False:
            frame.loc[:,'beta']=(frame['Roughness']*frame['Gustiness']**2)/((0.4/(np.log(10/frame['Roughness'])-frame['stability1']))**2)
        return frame
        
    def gust(self, clean31):
        '''calculated over a period of 50min'''
        
        gust=[]
        speed='WIND SPEED'+str(self.heights[0])+'(m/s)'
        for i in range(len(clean31[speed])):
            if i==0:
                g=(np.std([clean31.loc[i, speed], clean31.loc[i+1, speed], clean31.loc[i+2, speed]]))/clean31.loc[i, speed]
            elif i==1:
                g=(np.std([clean31.loc[i, speed], clean31.loc[i+1, speed], clean31.loc[i+2, speed], clean31.loc[i-1, speed]]))/clean31.loc[i, speed]
            elif i==len(clean31[speed])-2:
                g=(np.std([clean31.loc[i, speed], clean31.loc[i-1, speed], clean31.loc[i-2, speed], clean31.loc[i+1, speed]]))/clean31.loc[i, speed]
            elif i==len(clean31[speed])-1:
                g=(np.std([clean31.loc[i,speed], clean31.loc[i-1, speed], clean31.loc[i-2, speed]]))/clean31.loc[i, speed]
            else:
                g=(np.std([clean31.loc[i, speed], clean31.loc[i+1, speed], clean31.loc[i+2, speed], clean31.loc[i-1, speed], clean31.loc[i-2, speed]]))/clean31.loc[i, speed]
            gust.append(g)
        clean31.loc[:, 'Gustiness']=gust
        return clean31
        
    def phase_speed(self, clean31):
        
        clean31.loc[:, 'Phase_speed']=clean31['WAVELENGHT(m)']/clean31['WAVEPERIOD(s)']
        return clean31
        
    def wave_age(self, frame):
        
        frame.loc[:, 'wave_age']=frame['Phase_speed']/frame['insitu_friction'].replace(0, np.nan)
        return frame
    
    def relative_speed(self, clean31):
        '''To calculate re lative speed I need current measurements, phase speed is not valid. Until then, relative speed can be considered wind speed since U0 use to be very small in comparison with wind speed'''
        #this is not correct!!!!!!!!!!!!!!!! real way to find Ur is done in Lifting.drift_speed
        speed='WIND SPEED'+str(self.heights[0])+'(m/s)'
        clean31.loc[:, 'Relative_speed(m/s)']=list(clean31[speed])
        return clean31        
        
    def k_viscosity(self, frame):
            
        frame.loc[:,'dry_density']=(frame['PRESSURE(hPa)']*100)/(287.05*(frame['TEMPERATURE(C)']+273.15)) #result in kg/m3
        frame.loc[:,'density']=(frame['dry_density']*(1+frame['HUMIDITY(%)']/100))/(1+((frame['HUMIDITY(%)']/100)*461.5/287.05))
        frame.loc[:,'viscosity']=((1.458*10**-6)*((frame['TEMPERATURE(C)']+273.15)**(3./2)))/(frame['TEMPERATURE(C)']+ 273.15 + 110.4)
        frame.loc[:,'kinematic']=frame['viscosity']/frame['density']
        return frame
            
    def insitu_friction(self, frame):
        '''Calculates friction velocity through horizontal and vertical velocities''' 

        if 'HORIZONTAL_SPEED(m/s)' and 'VERTICAL_SPEED(m/s)' in frame.columns:
            #till here horizontal speed is calculated at measurement height, knowing surface roughness I can calculate horizontal speed at 10m, vertical speed is supposed to be the same or almost
            h=input('Height of horizontal speed measurement(m): ')
            frame.set_index('Date', inplace=True, drop=False)
            frame.sort_index(inplace=True)
            frame.loc[:, 'HORIZONTAL_SPEED_10(m/s)']=frame['HORIZONTAL_SPEED(m/s)']*((np.log(10/frame['Roughness']))/(np.log(h/frame['Roughness'])))
            times=[-20,-10,0,10,20]
            friction=[]
            for z, row in frame.iterrows():
                product=[]
                hori=[]
                verti=[]
                for i in times: #to calculate mean horizontal and vertical speeds
                    try:
                        time=row['Date']+datetime.timedelta(minutes=i)
                        h=frame.ix[time]['HORIZONTAL_SPEED_10(m/s)']
                        hori.append(h)
                        v=frame.ix[time]['VERTICAL_SPEED(m/s)']
                        verti.append(v)
                    except KeyError:
                        continue
                H=np.average(hori)
                V=np.average(verti)
                for i in times:# to calculate mean product of speeds
                    try:
                        time=row['Date']+datetime.timedelta(minutes=i)
                        vel=(frame.ix[time]['HORIZONTAL_SPEED_10(m/s)']-H)*(frame.ix[time]['VERTICAL_SPEED(m/s)']-V)
                        product.append(vel)
                    except KeyError:
                        continue    
                if len(product)<=1:
                    fric=np.nan
                else:
                    fric=abs((sum(product)/len(product)))**(1./2)                
                friction.append(fric)
            frame.loc[:, 'u*']=friction
            frame.reset_index(inplace=True, drop=True)
            
        else:
            pass
        return frame
        
    def drag_insitu(self, frame):
        '''By the moment I'm not using gustiness'''
        
        if self.term=='long':
            #frame['Cd_insitu']=((np.average(frame['insitu_friction']**2))/(np.average(frame['Gustiness'])*np.average(frame['Relative_speed(m/s)'])**2))*1000
            frame['Cd_insitu']=((np.average(frame['insitu_friction']**2))/(1*np.average(frame['Relative_speed(m/s)'])**2))*1000            
        elif self.term=='instant':
            #frame['Cd_insitu']=((frame['insitu_friction']**2)/(frame['Gustiness']*frame['Relative_speed(m/s)']**2))*1000
            frame.loc[:, 'Cd_insitu']=((frame['insitu_friction']**2)/(1*frame['Relative_speed(m/s)']**2))*1000
        return frame
    
    def friction(self, frame, stability=0):
        '''Calculates friction velocity through the log law since roughness is already known through log law with two different heights'''
        
        for tru in frame.columns:
            check=re.findall(r'\d+', tru)
            if str(self.heights[0]) in check and 'SPEED' in tru:
                spd1=tru
        if self.term=='long':
            frame['insitu_friction']=(0.4*np.average(frame[spd1]))/((np.log(self.heights[0]/np.average(frame['Roughness'])))-stability)        
        elif self.term=='instant':
            g=self.gen_friction(frame['Roughness'], frame[spd1], stability)
            frame.loc[:,'insitu_friction' ]=list(g)
        return frame
        
    def gen_friction(self, xx, yy, stability):
        '''calculation of friction velocity trough log law,  xx=roughness, yy=wspeed'''        
        
        for i, z in enumerate(zip(xx, yy)):
            warnings.filterwarnings('error')
            if i==0:
                values=[0,1,2]
            elif i==1:
                values=[-1,0,1,2]
            elif i==len(yy)-2:
                values=[-2,-1,0,1]
            elif i==len(yy)-1:
                values=[-2,-1,0]
            else:
                values=[-2,-1,0,1,2]
            avg=[list(yy)[i+x] for x in values] 
            try:
                fric=(0.4*np.average(avg))/((np.log(self.heights[0]/z[0]))-stability)
            except RuntimeWarning:
                fric=np.nan
            yield fric
     
    def select_cell(self, df):
        
        celling=Merging(self.sats, self.coord, self.dataframe)
        cells_array=celling.set_grid()
        centre=[self.cordis[0]+180, self.cordis[1]+90] #calculate center of the square
        celda=cells_array[KDTree(cells_array).query(centre)[1]]#return the closest cell to my point
        cell=[celda[0]-180, celda[1]-90]
        cell_name=''.join([str(cell[0]), '/', str(cell[1])])
        df.loc[:, 'cell_center']=cell_name
        return df

    def execution(self):
        
        self.select_cordis()
        self.select_heights()
        self.preparing()
        filepath=raw_input('Full, absolute path to csv file to keep filtered dataframe:')
        self.dataframe.to_csv(filepath)
        return (self.dataframe, self.heights[-1])
        
        
class Insitu_calcs:
    
    def __init__(self, basis, months, year, dataframe, term='long', period=None):
        
        self.calc_df=object()
        self.dates=[]
        self.hspeeds=[]
        self.basis=basis
        self.df=dataframe
        self.year=year
        self.months=months
        self.period=period
        self.term=term
            
    def new_frame(self, data):
        
        levels=list(data.index.names)
        cells=data.index.get_level_values(levels[0]).unique()
        devices=data.index.get_level_values(levels[1]).unique()
        dates=self.dates        
        A=len(cells)
        B=len(devices)
        C=len(dates)        
        level1=[]
        level2=[]
        level3=[]
        
        if len(levels) == 2:
            for i in range(A):
                a=0
                while a<B:
                    level1.append(cells[i])
                    a+=1
            level2=list(devices)            
            indexes=pd.MultiIndex.from_arrays([level1, level2*A], names=levels)
            
        elif len(levels) == 3:
            for i in range(A):
                a=0
                while a<(B*C):
                    level1.append(cells[i])
                    a+=1
            for j in range(B):
                a=0
                while a<C:
                    level2.append(devices[j])
                    a+=1   
            level3=list(dates)            
            indexes=pd.MultiIndex.from_arrays([level1, level2*A, level3*(A*B)], names=levels)
            
        elif len(levels) == 4:
            days=['day', 'night']
            #days=data.index.get_level_values(levels[3]).unique()
            D=len(days)
            for i in range(A):
                a=0
                while a<(B*C*D):
                    level1.append(cells[i])
                    a+=1
            for j in range(B):
                a=0
                while a<(C*D):
                    level2.append(devices[j])
                    a+=1   
            for k in range(C):
                a=0
                while a<(D):
                    level3.append(dates[k])
                    a+=1   
            level4=days           
            indexes=pd.MultiIndex.from_arrays([level1, level2*A, level3*(A*B), level4*(A*B*C)], names=levels)
        
        cols=[['Temperature', 'Temperature', 'Temperature', 'Temperature', 'Pressure', 'Pressure', 'Pressure', 'Pressure', 'Humidity', 'Humidity', 'Humidity', 'Humidity', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed2', 'Wspeed3', 'Wspeed4', 'Wspeed5'], ['Average', 'Min', 'Max', 'Sdeviation', 'Average', 'Min', 'Max', 'Sdeviation', 'Average', 'Min', 'Max', 'Sdeviation', 'Average', 'Min', 'Max', 'Sdeviation', 'Samples', 'Roughness', 'Hubspeed', 'C', 'K', 'AED', 'WPD', 'Effective_ws', 'WPD_100', 'WPD_200', 'Average', 'Average', 'Average', 'Average']]
        self.calc_df=DataFrame(index=indexes, columns=cols)
        
    def set_dates(self):
        
        mesos={'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6, 'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
        meses=list(self.months)
        yes=list(self.year)
        years=set()
        if yes[0]=='All':
            annos=self.df['Date'].unique()
            for i in annos:
                try:
                    foo=i.year
                except AttributeError:
                    foo=parser.parse(i).year
                years.add(str(foo))
        elif yes[0]=='None':
            pass            
        else:
            for i in yes:
                years.add(str(i))
                
        if meses[0]=='All' and yes[0]!='None':
            for j in range(1,13):
                    for q in years:
                        bas=''.join([str(j), '/', str(q)])
                        self.dates.append(bas)
        elif meses[0]=='None' and yes[0]!='None':
            self.dates=list(years)
        elif meses[0]!='None' and meses[0]!='All' and yes[0]!='None':
            for j in self.months:
                    for q in years:
                        bas=''.join([str(mesos[j]), '/', str(q)])
                        self.dates.append(bas)
        elif meses[0]=='All' and yes[0]=='None':
            self.dates=[1,2,3,4,5,6,7,8,9,10,11,12]
        elif meses[0]!='None' and meses[0]!='All' and yes[0]=='None':  
            self.dates=[mesos[x] for x in meses]
        elif meses[0]=='None' and yes[0]=='None':
            pass

    def sat_weibull(self, std, mean, meanhub):
        
        K=(std/mean)**(-1.086)
        j=(1+(1/K))
        C=meanhub/(special.gamma(j))
        return (K, C)
        
    def aed(self, A, K, density=1.225):
        
        prod=1+(3/K)
        coef=special.gamma(prod)
        E=0.5*density*coef*(A**3)
        return E
        
    def wpd(self, speed, density=1.225):
        
        E=0.5*density*(speed**3)
        return E
        
    def ocurrence(self, series, bins, position=1):
        
        try:
            if len(series)==1 or series.dtype==np.float64:
                out=1
            else:
                seri=pd.value_counts(pd.cut(series, bins=bins), normalize=True).sort_index()
                out=seri.ix[position]
        except TypeError:
            out=1
        return out*100
        
    def def_speeds(self):
        
        cols=list(self.df.columns)
        for i in cols:
            if i[5:10]=='SPEED':
                self.hspeeds.append(i)
            else:
                continue
            
    def insitu_by_period(self):
        '''Indexing by date and time, and then same as sat_all_years'''
        
        if self.period[0]!=None and self.period[2]!=None:
            DFrame=self.df.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            framing=DF[self.period[0]:self.period[1]]
            dframing=framing.set_index('Time', drop=False)
            frame=dframing.sort_index()
            table=frame[self.period[2]:self.period[3]]
        elif self.period[0]!=None and self.period[2]==None:
            DFrame=self.df.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[0]:self.period[1]]
        elif self.period[0]==None and self.period[2]!=None:
            DFrame=self.df.set_index('Time', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[2]:self.period[3]]
        self.df=table
    
    def insitu_all_years(self):
        
        DF=self.df.set_index(['cell_center', 'Device'])
        self.new_frame(DF)
        cells=DF.index.get_level_values('cell_center').unique()
        devices=DF.index.get_level_values('Device').unique()
       
        for row in cells:
            for dev in devices:
                try:
                    self.calc_df.set_value((row, dev), ('Temperature', 'Average'), np.average(DF['TEMPERATURE(C)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Temperature', 'Min'), np.amin(DF['TEMPERATURE(C)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Temperature', 'Max'), np.amax(DF['TEMPERATURE(C)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Temperature', 'Sdeviation'), np.std(DF['TEMPERATURE(C)'].ix[row].ix[dev].dropna()))
                except (KeyError, IndexError):
                    pass
                try:
                    self.calc_df.set_value((row, dev), ('Pressure', 'Average'), np.average(DF['PRESSURE(hPa)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Pressure', 'Min'), np.amin(DF['PRESSURE(hPa)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Pressure', 'Max'), np.amax(DF['PRESSURE(hPa)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Pressure', 'Sdeviation'), np.std(DF['PRESSURE(hPa)'].ix[row].ix[dev].dropna()))
                except (KeyError, IndexError):
                    pass
                try:
                    self.calc_df.set_value((row, dev), ('Humidity', 'Average'), np.average(DF['HUMIDITY(%)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Humidity', 'Min'), np.amin(DF['HUMIDITY(%)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Humidity', 'Max'), np.amax(DF['HUMIDITY(%)'].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Humidity', 'Sdeviation'), np.std(DF['HUMIDITY(%)'].ix[row].ix[dev].dropna()))
                except (KeyError, IndexError):
                    pass
                try:
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Average'), np.average(DF[self.hspeeds[0]].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Wspeed2', 'Average'), np.average(DF[self.hspeeds[1]].ix[row].ix[dev].dropna()))
                except  (KeyError, IndexError):
                    continue
                try:
                    self.calc_df.set_value((row, dev), ('Wspeed3', 'Average'), np.average(DF[self.hspeeds[2]].ix[row].ix[dev].dropna()))
                except (KeyError, IndexError):
                    pass
                try:
                    self.calc_df.set_value((row, dev), ('Wspeed4', 'Average'), np.average(DF[self.hspeeds[3]].ix[row].ix[dev].dropna()))
                    self.calc_df.set_value((row, dev), ('Wspeed5', 'Average'), np.average(DF[self.hspeeds[4]].ix[row].ix[dev].dropna()))
                except(KeyError, IndexError):
                    pass
                try:
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Hubspeed'), np.average(DF['Wlifted1'].ix[row].ix[dev].dropna()))
                    if self.term=='long':
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Min'), np.amin(DF['Wspd1'].ix[row].ix[dev].dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Max'), np.amax(DF['Wspd1'].ix[row].ix[dev].dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Sdeviation'), np.std(DF['Wspd1'].ix[row].ix[dev].dropna()))
                        K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev], np.average(DF['Wspd1'].ix[row].ix[dev].dropna()), self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev])
                    elif self.term=='instant':
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Min'), np.amin(DF['Wlifted1'].ix[row].ix[dev].dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Max'), np.amax(DF['Wlifted1'].ix[row].ix[dev].dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Sdeviation'), np.std(DF['Wlifted1'].ix[row].ix[dev].dropna()))
                        K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev])
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'AED'), self.aed(C, K))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev], [0, 4, 25, 100]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev]), [0, 100, 5000]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev]), [0, 200, 5000]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Roughness'), np.average(DF['Roughness'].ix[row].ix[dev].dropna()))                   
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Samples'), len(DF['Wlifted1'].ix[row].ix[dev].dropna()))                    
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'C'), C)
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'K'), K)
                except IndexError:
                    continue
                
    def insitu_by_dates(self):
        '''By dates means to select by years or months, dates are already set'''
        
        if self.months[0]!='None' and self.year[0]=='None':
            self.df['Month']=self.df['Date'].dt.month
            DF=self.df.set_index(['cell_center', 'Device', 'Month'])
        elif self.year[0]!='None':
            DF=self.df.set_index(['cell_center', 'Device', 'Date'])
        self.new_frame(DF)
        cells=DF.index.get_level_values('cell_center').unique()
        devices=DF.index.get_level_values('Device').unique()      
        #self.calc_df.index.lexsort_depth
        #self.calc_df.sortlevel(0).lexsort_depth
        
        for row in cells:
            for dev in devices:
                for date in self.dates:
                    try:
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Average'), np.average(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Min'), np.amin(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Max'), np.amax(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Sdeviation'), np.std(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Average'), np.average(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Min'), np.amin(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Max'), np.amax(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Sdeviation'), np.std(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Average'), np.average(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Min'), np.amin(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Max'), np.amax(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Sdeviation'), np.std(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Average'), np.average(DF[self.hspeeds[0]].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Wspeed2', 'Average'), np.average(DF[self.hspeeds[1]].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        continue
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed3', 'Average'), np.average(DF[self.hspeeds[2]].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed4', 'Average'), np.average(DF[self.hspeeds[3]].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Wspeed5', 'Average'), np.average(DF[self.hspeeds[4]].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Hubspeed'), np.average(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                        if self.term=='long':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], np.average(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()), self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        elif self.term=='instant':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'AED'), self.aed(C, K))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev].ix[date], [0, 4, 25, 100]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 100, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 200, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Roughness'), np.average(DF['Roughness'].ix[row].ix[dev].ix[date].dropna()))                       
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Samples'), len(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))                        
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'C'), C)
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'K'), K)
                    except (KeyError, IndexError):
                        continue

                
    def insitu_by_daynight(self):
        
        DF=self.df.set_index(['cell_center', 'Device', 'Day/Night'])
        self.new_frame(DF)
        cells=DF.index.get_level_values('cell_center').unique()
        devices=DF.index.get_level_values('Device').unique()
        dia=[]
        if self.basis=='All':
            dia=['day', 'night']
        else:
            dia.append(self.basis)
        
        for row in cells:
            for dev in devices:
                for date in dia:
                    try:
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Average'), np.average(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Min'), np.amin(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Max'), np.amax(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Temperature', 'Sdeviation'), np.std(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Average'), np.average(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Min'), np.amin(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Max'), np.amax(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Pressure', 'Sdeviation'), np.std(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Average'), np.average(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Min'), np.amin(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Max'), np.amax(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Humidity', 'Sdeviation'), np.std(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Average'), np.average(DF[self.hspeeds[0]].ix[row].ix[dev].ix[date].dropna()))
                        self.calc_df.set_value((row, dev, date), ('Wspeed2', 'Average'), np.average(DF[self.hspeeds[1]].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        continue
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed3', 'Average'), np.average(DF[self.hspeeds[2]].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed4', 'Average'), np.average(DF[self.hspeeds[3]].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed5', 'Average'), np.average(DF[self.hspeeds[4]].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        pass
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Hubspeed'), np.average(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                        if self.term=='long':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], np.average(DF['Wspd1'].ix[row].ix[dev].ix[date].dropna()), self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        elif self.term=='instant':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'AED'), self.aed(C, K))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev].ix[date], [0, 4, 25, 100]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 100, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 200, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Roughness'), np.average(DF['Roughness'].ix[row].ix[dev].ix[date].dropna()))                        
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Samples'), len(DF['Wlifted1'].ix[row].ix[dev].ix[date].dropna()))                        
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'C'), C)
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'K'), K)
                    except(KeyError, IndexError):
                        continue
    
    def insitu_by_date_and_night(self):
        
        if self.months[0]!='None' and self.year[0]=='None':
            self.df['Month']=self.df['Date'].dt.month
            DF=self.df.set_index(['cell_center', 'Device', 'Month', 'Day/Night'])
        elif self.year[0]!='None':
            DF=self.df.set_index(['cell_center', 'Device', 'Date', 'Day/Night'])
        self.new_frame(DF)
        cells=DF.index.get_level_values('cell_center').unique()
        devices=DF.index.get_level_values('Device').unique()
        dia=DF.index.get_level_values('Day/Night').unique()
            
        for row in cells:
            for dev in devices:
                for date in self.dates:
                    for base in dia:
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Temperature', 'Average'), np.average(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Temperature', 'Min'),np.amin(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Temperature', 'Max'),np.amax(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Temperature', 'Sdeviation'),np.std(DF['TEMPERATURE(C)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except ( KeyError, IndexError):
                            pass
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Pressure', 'Average'), np.average(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Pressure', 'Min'), np.amin(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Pressure', 'Max'), np.amax(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Pressure', 'Sdeviation'), np.std(DF['PRESSURE(hPa)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            pass
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Humidity', 'Average'), np.average(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Humidity', 'Min'), np.amin(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Humidity', 'Max'), np.amax(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Humidity', 'Sdeviation'), np.std(DF['HUMIDITY(%)'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            pass 
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Average'), np.average(DF[self.hspeeds[0]].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed2', 'Average'), np.average(DF[self.hspeeds[1]].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            continue
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed3', 'Average'), np.average(DF[self.hspeeds[2]].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            pass
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed4', 'Average'), np.average(DF[self.hspeeds[3]].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            pass
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed5', 'Average'), np.average(DF[self.hspeeds[4]].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            pass
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Hubspeed'), np.average(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            if self.term=='long':
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Min'), np.amin(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Max'), np.amax(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Sdeviation'), np.std(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                                K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date].ix[base], np.average(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base].dropna()), self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base])
                            elif self.term=='instant':
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Min'), np.amin(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Max'), np.amax(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Sdeviation'), np.std(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                                K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date].ix[base], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base])
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'AED'), self.aed(C, K))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base], [0, 4, 25, 100]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]), [0, 100, 5000]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]), [0, 200, 5000]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Roughness'), np.average(DF['Roughness'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Samples'), len(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base].dropna()))                            
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'C'), C)
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'K'), K)
                        except (KeyError, IndexError):
                            continue
    
    def execution(self):
        
        self.def_speeds()
        if self.period!=None:
            self.insitu_by_period()
        self.set_dates()
        if self.months[0]=='None' and self.basis=='None' and self.year[0]=='None':
            self.insitu_all_years()
        elif self.months[0]!='None' or self.year[0]!='None' and self.basis=='None':
            self.insitu_by_dates()
        elif self.months[0]=='None' and self.year[0]=='None' and self.basis!='None':
            self.insitu_by_daynight()
        elif self.months[0]!='None' or self.year[0]!='None' and self.basis!='None':
            self.insitu_by_date_and_night()
        else:
            sys.exit('No calculations')
        self.calc_df.sort_index(level='cell_center', inplace=True)    
        return self.calc_df            
                

class Overlapping:
    '''This class is used to select the insitu data that overlaps with satellite data'''

    def __init__(self, frame_sat, frame_insi, period, coords):
        
        try:
            DFsat=frame_sat.reset_index()
        except ValueError:
            DFsat=frame_sat
        try:
            self.DFsat=DFsat.drop('ID', axis=1)
        except (KeyError, ValueError):
            self.DFsat=DFsat
        try:
            self.DFinsitu=frame_insi.drop('ID', axis=1)
        except (KeyError, ValueError):
            self.DFinsitu=frame_insi
        self.period=period
        self.coord=coords
        
    def insitu_by_period(self, df):
        '''Indexing by date and time'''

        if self.period[0]!=None and self.period[2]!=None:
            DFrame=df.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            framing=DF[self.period[0]:self.period[1]]
            dframing=framing.set_index('Time', drop=False)
            frame=dframing.sort_index()
            table=frame[self.period[2]:self.period[3]]
        elif self.period[0]!=None and self.period[2]==None:
            DFrame=df.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[0]:self.period[1]]
        elif self.period[0]==None and self.period[2]!=None:
            DFrame=df.set_index('Time', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[2]:self.period[3]]
        return table
        
    def filter_insitu(self, df):
        '''Build the filtered, insitu dataframe'''
        
        satels=list(df['Device'].unique())
        lista=[]
        missing=set()
        dates_times=[]
        Dafa=df.reset_index(drop=True)
        Dafa.set_index('cell_center', inplace=True, drop=False)
        DF=Dafa.ix[self.select_cell()].reset_index(drop=True)
        check=raw_input('Do you want to check overlapping for specific satellite?(y/n): ')
        if check=='y':
            sat=raw_input('Choose satellite '+str(satels)+': ')
            while sat in satels:
                break
            else:
                print 'Wrong name'
                sat=raw_input('Choose satellite '+str(satels)+': ')
            DF.set_index('Device', inplace=True, drop=False)
            DF=DF.ix[sat].reset_index(drop=True)
        else:
            pass
        
        self.DFinsitu.set_index('Timestamp', inplace=True, drop=False)
        insitu=self.DFinsitu.sort_index()
        stamps=DF['Timestamp']
        for i in range(len(stamps)):
            try:
                before=stamps[i]-datetime.timedelta(minutes=4, seconds=59)#setting before and later it's chosen the accepted interval of time to stablish overlapped measurements
                later=stamps[i]+datetime.timedelta(minutes=5, seconds=1)
                row=insitu.ix[before:later]
                
                #doing this, I'm gonna use measurements as an average of 50 min
                second_previous=insitu.ix[row['Timestamp']-datetime.timedelta(minutes=20)]
                previous_row=insitu.ix[row['Timestamp']-datetime.timedelta(minutes=10)]
                next_row=insitu.ix[row['Timestamp']+datetime.timedelta(minutes=10)]
                second_next=insitu.ix[row['Timestamp']+datetime.timedelta(minutes=20)]
                mix=pd.concat([row, previous_row, next_row, second_previous, second_next])
                mix.reset_index(drop=True, inplace=True)
                mix.drop(['Date', 'Time', 'Timestamp', 'Device', 'cell_center', 'Day/Night', 'Cd_insitu', 'insitu_friction'], axis=1, inplace=True)
                angles={}
                for x in mix.columns:
                    if 'WIND DIRECTION' in x:
                        angle=Commons.avg_angles(mix.ix[0][x], mix.ix[1][x], mix.ix[2][x], mix.ix[3][x], mix.ix[4][x])
                        angles[x]=angle
                        mix.drop(x, axis=1, inplace=True)
                    else:
                        pass
                mix.loc[9]=mix.mean()#here I have used 10, since I do the mean of 5 rows or measurements with a 6 could be enough, but with 10 am allowing mean of 9 rows if necessary, more than 9 rows doesn't make sense
                line=mix.drop([0,1,2,3,4])
                for j in angles:
                    line[j]=angles[j]
                line.reset_index(drop=True, inplace=True)
                row.reset_index(drop=True, inplace=True)
                col_list=['Date', 'Time', 'Timestamp', 'Device', 'cell_center', 'Day/Night', 'Cd_insitu', 'insitu_friction']
                row=row[col_list]
                linia=pd.concat([line, row], axis=1)
            except (KeyError, IndexError): #IndexError was include to avoid empty dataframes or row variable
                missing.add(i)#This means no date, time in insitu frame, probably because of failure of insitu instruments
                continue
            try:
                if linia['Timestamp'].ix[0] in dates_times:#These represents satellite measurements at almost same time (so repeated), or at different second or minute, but in the same interval, betwwen before:after
                    missing.add(i) 
                    continue
                else:
                    dates_times.append(linia['Timestamp'].ix[0])
                    lista.append(linia)
            except (IndexError, KeyError):
                missing.add(i)#This means no data, there is row with selected date, time in insitu frame but that row is empty
                continue
        insitu_frame=pd.concat(lista, ignore_index=True)
        insi=insitu_frame.sort_values(by='Timestamp')
        insi['ID']=range(len(insitu_frame))
        insitu_frame=insi
        sat_frame=DF.drop(list(missing))
        sat=sat_frame.sort_values(by='Timestamp')
        sat['ID']=range(len(sat))
        sat_frame=sat
        print str(len(insitu_frame['ID']))+' overlapments'
        
        return insitu_frame, sat_frame
        
    def choose_cell(self):
        '''Asking user from waht cell wants to compare overlapping''' 
        
        cell=[]
        print '\nWhat cell you want to use for satellite data? Choose coordinates:'
        h1=input('\tLongitude:')
        h2=input('\tLatitude:')
        cell.append(h1)
        cell.append(h2)
        return cell
        
    def select_cell(self, df=None):
        
        resolution=raw_input('Choose resolution of grid (0.02, 0.16, 0.25 or None): ')
        if resolution=='0.16':
            sats=['Rapidscat']
        elif resolution=='0.25':
            sats=['Windsat']
        else:
            sats=['All']
        celling=Merging(sats, self.coord, df)
        cells_array=celling.set_grid()
        cordis=self.choose_cell()
        centre=[cordis[0]+180, cordis[1]+90] #calculate center of the square
        celda=cells_array[KDTree(cells_array).query(centre)[1]]#return the closest cell to my point
        cell=[celda[0]-180, celda[1]-90]
        cell_name=''.join([str(cell[0]), '/', str(cell[1])])
        return cell_name
        
    def execution(self):
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Selecting overlapped rows >>>'
        DFsat=self.insitu_by_period(self.DFsat)
        insitu, sat=self.filter_insitu(DFsat)
        return insitu, sat
        
        
                         

            

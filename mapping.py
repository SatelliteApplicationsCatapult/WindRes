# -*- coding: utf-8 -*-
"""
Created on Wed Dec 09 15:08:06 2015

@author: ftb14219
"""

from mpl_toolkits.basemap import Basemap, cm
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import itertools

class Wind_map:
    
    def __init__(self, dataframe, coordinates, height):
        
        self.df=dataframe
        self.coords=coordinates
        self.height=height
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Calculating raster layer >>>' 
        
    def raster(self, df):
        
        levels=list(df.index.names)
        num=len(levels)
        buf=df.reset_index()
        longis=set() #not repeated
        lon=[]
        latis=set() #not repeated
        lat=[]
        for item in buf['cell_center']:
            a=item.split('/')
            lon.append(float(a[0]))
            lat.append(float(a[1]))
            longis.add(float(a[0]))
            latis.add(float(a[1]))
        Longitude=sorted(list(longis))
        Latitude=sorted(list(latis))
        buf['Long']=pd.Series(lon)
        buf['Lat']=pd.Series(lat)
        levels.remove('cell_center')
        levels.extend(['Lat', 'Long'])
        DF=buf.set_index(levels)
        mapa=self.set_square()
        
        if num==2:
            devs=DF.index.get_level_values(0).unique()
            for dev in devs:
                arr=[]
                tab=[]
                for i in Latitude:
                    line=[]
                    linia=[]
                    for j in Longitude:
                        try:
                            ws=DF['Wspeed1']['Hubspeed'].ix[dev].ix[i].ix[j]
                        except KeyError:
                            ws=None
                        try:
                            ss=DF['Wspeed1']['Samples'].ix[dev].ix[i].ix[j]
                        except KeyError:
                            ss=None
                        line.append(ws)
                        linia.append(ss)
                    arr.append(line)
                    tab.append(linia)
                    array_speed=np.array(arr)
                    array_dens=np.array(tab)
                lab=[dev]                
                self.mapping(Longitude, Latitude, array_speed, mapa, lab)
                self.mapping(Longitude, Latitude, array_dens, mapa, lab, density=True)
                self.export(Longitude, Latitude, array_speed, lab)
                
                
        elif num==3:
            devs=DF.index.get_level_values(0).unique()
            dates=DF.index.get_level_values(1).unique()
            for dev in devs:
                for date in dates:
                    arr=[]
                    tab=[]
                    for i in Latitude:
                        line=[]
                        linia=[]
                        for j in Longitude:
                            try:
                                ws=DF['Wspeed1']['Hubspeed'].ix[dev].ix[date].ix[i].ix[j]
                            except KeyError:
                                ws=None
                            try:
                                ss=DF['Wspeed1']['Samples'].ix[dev].ix[date].ix[i].ix[j]
                            except KeyError:
                                ss=None
                            line.append(ws)
                            linia.append(ss)
                        arr.append(line)
                        tab.append(linia)
                        array_speed=np.array(arr)
                        array_dens=np.array(tab)
                    lab=[dev, date]
                    self.mapping(Longitude, Latitude, array_speed, mapa, lab)
                    self.mapping(Longitude, Latitude, array_dens, mapa, lab, density=True)
                    self.export(Longitude, Latitude, array_speed, lab)
                    
                    
        elif num==4:
            devs=DF.index.get_level_values(0).unique()
            dates=DF.index.get_level_values(1).unique()
            day=DF.index.get_level_values(2).unique()
            for dev in devs:
                for date in dates:
                    for base in day:
                        arr=[]
                        tab=[]
                        for i in Latitude:
                            line=[]
                            linia=[]
                            for j in Longitude:
                                try:
                                    ws=DF['Wspeed1']['Hubspeed'].ix[dev].ix[date].ix[base].ix[i].ix[j]
                                except KeyError:
                                    ws=None
                                try:
                                    ss=DF['Wspeed1']['Samples'].ix[dev].ix[date].ix[base].ix[i].ix[j]
                                except KeyError:
                                    ss=None
                                line.append(ws)
                                linia.append(ss)
                            arr.append(line)
                            tab.append(linia)
                            array_speed=np.array(arr)
                            array_dens=np.array(tab)
                        lab=[dev, date, base]
                        self.mapping(Longitude, Latitude, array_speed, mapa, lab)
                        self.mapping(Longitude, Latitude, array_dens, mapa, lab, density=True)
                        self.export(Longitude, Latitude, array_speed, lab)
                        
                        
                        
    def set_square(self):
        
        mapis=Basemap(projection='merc', lon_0=((self.coords[0]+self.coords[1])/2)-180, lat_0=((self.coords[2]+self.coords[3])/2)-90, 
                      resolution='h', area_thresh=0.1, llcrnrlon=self.coords[0]-180, urcrnrlon=self.coords[1]-180, llcrnrlat=self.coords[2]-90, urcrnrlat=self.coords[3]-90)
        return mapis       
    
    def mapping(self, x, y, data, mapa, labels, density=False):
        
        if density==False:
            if len(labels)==1:
                title='Mean wind speed map by '+str(labels[0])+' at '+str(self.height)+'m'
            elif len(labels)==2:
                title='Mean wind speed map by '+str(labels[0])+' on '+str(labels[1])+' at '+str(self.height)+'m'
            elif len(labels)==3:
                title='Mean wind speed map by '+str(labels[0])+' on '+str(labels[1])+' during '+str(labels[2])+' at '+str(self.height)+'m'
            labis='(m/s)'
            steps=np.arange(0,30,0.5)
            paleta=plt.cm.jet
        elif density==True:
            if len(labels)==1:
                title='Data density map by '+str(labels[0])
            elif len(labels)==2:
                title='Data density map by '+str(labels[0])+' on '+str(labels[1])
            elif len(labels)==3:
                title='Data density map by '+str(labels[0])+' on '+str(labels[1])+' during '+str(labels[2])
            labis='Number of measurements'
            steps=[0, 5, 20, 50, 100, 200, 300, 400, 500, 600, 800, 1000, 1200, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000]
            paleta=cm.s3pcpn
            
        fig=plt.figure(figsize=(20,20), dpi=150)
        fig.add_axes([0.1,0.1,0.8,0.8])
        mapa.drawcoastlines()
        mapa.fillcontinents(color='grey')
        mapa.drawmapboundary()
        mapa.drawmeridians(np.arange(0, 360, 0.5), labels=[0,0,0,1])
        mapa.drawparallels(np.arange(-90, 90, 0.5), labels=[1,0,0,0])
        xx, yy=np.meshgrid(x,y)
        lis=mapa.contourf(xx, yy, data, steps, cmap=paleta, latlon=True)
        cbar=mapa.colorbar(lis, location='right')
        cbar.set_label(labis)
         
        plt.title(title)
        plt.xlabel('Longitude', labelpad=30)
        plt.ylabel('Latitude', labelpad=40)
        plt.show()
        
        
    def export(self, x, y, data, labels):
        
        dataframe=pd.DataFrame()
        dataframe['Lat']=np.repeat(y,len(x))
        dataframe['Long']=x*len(y)        
        speed=list(itertools.chain(*data))
        dataframe['Wspeed']=pd.Series(speed)
        
        path=raw_input('Full, absolute path to csv folder where to keep file for Qgis:')
        if path=='':
            pass
        else:
            if len(labels)==1:
                title='Wind_csv_'+str(labels[0])
            elif len(labels)==2:
                title='Wind_csv_'+str(labels[0])+'/'+str(labels[1])
            elif len(labels)==3:
                title='Wind_csv_'+str(labels[0])+'/'+str(labels[1])+'/'+str(labels[2])
            filepath=''.join([path, '/', title, '.csv'])
            dataframe.to_csv(filepath)
            #exporting same data but tab separeted values(TAB) instead of commas(CSV)
            tabpath=''.join([path, '/', title, '.tab'])
            with open(filepath) as infile:  
                with open(tabpath, mode="w") as outfile:
                    for row in infile:
                        fields = row.split(',')
                        outfile.write('\t'.join(fields))
        
        
    def execution(self):
        
        self.raster(self.df)
        
                    
                
        
        
            
            
        
    
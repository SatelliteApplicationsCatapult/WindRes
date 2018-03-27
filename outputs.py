# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 15:23:08 2015

@author: ftb14219
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
from scipy.spatial import KDTree
import dateutil.parser as parser
from scipy import stats
#import matplotlib.cm as cm

class Plotting:
    
    def __init__(self, frame, rawframe, months, years, height, term='long', period=None):
        #frame is the df with calculated results, rawframe still mantain wind diretions
        # but use only Wlifted for insitu and Wlifted1 for satellites when plotting windroses
        
        self.cell=[]
        self.selected_cell=[]
        self.dates=[]
        self.frame=frame
        self.months=months
        self.year=years
        self.choose_cell()
        self.height=height
        self.period=period
        self.term=term
        self.periods=self.periodically(period)
        if self.periods==None:
            self.raw=rawframe
            try:
                self.dates=list(self.frame.index.get_level_values('Date').unique())
            except KeyError:
                self.set_dates()
        else:
            self.raw=self.by_period(rawframe)
            
        '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Plotting data >>>' 
    
    def by_period(self, frame):
        '''Indexing by date and time, and then same as sat_all_years'''
        
        if self.period[0]!=None and self.period[2]!=None:
            DFrame=frame.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            framing=DF[self.period[0]:self.period[1]]
            dframing=framing.set_index('Time', drop=False)
            frame=dframing.sort_index()
            table=frame[self.period[2]:self.period[3]]
        elif self.period[0]!=None and self.period[2]==None:
            DFrame=frame.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[0]:self.period[1]]
        elif self.period[0]==None and self.period[2]!=None:
            DFrame=frame.set_index('Time', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[2]:self.period[3]]
        table=table.reset_index(drop=True)
        return table    
    
    def periodically(self, pe):
        '''Adapting period to titles'''
        
        if pe!=None:
            if pe[0]!=None and pe[2]!=None:
                foo=''.join([' during ', str(pe[0]), ':', str(pe[1]), ' between ', str(pe[2]), '-', str(pe[3])])
            elif pe[0]!=None and pe[2]==None:
                foo=''.join([' during ', str(pe[0]), ':', str(pe[1])])
            elif pe[0]==None and pe[2]!=None:
                foo=''.join([' between ', str(pe[2]), '-', str(pe[3])])
        else:
            foo=None
        return foo
            
        
    def choose_cell(self, local=False):
        '''Asking user from waht cell wants plots''' 
        
        if local==False:
            print '\nWhere you want to study wind resource? Choose coordinates:'
        else:
            print '\nWhat cell you want to use for satellite data? Choose coordinates:' 
        h1=input('\tLongitude (-180 to 180):')
        h2=input('\tLatitude (-90 to 90):')
        if local==False:
            self.cell.append(h1)
            self.cell.append(h2)
        else:
            cell=[h1, h2]
            return cell
        
    def select_cell(self, local=False):
        '''from chosen coordinates to cell grid coordinates'''
        
        cells=list(self.frame.index.get_level_values('cell_center').unique())
        if cells[0]=='No_cell':
            self.selected_cell.append('No_cell')
        else:
            cells_array=[]
            for i in cells:
                a=i.split('/')
                b=[]
                for j in a:
                    c=float(j)
                    b.append(c)
                cells_array.append(b)#here my cells_array boundary is (-180 to 180) and (-90 to 90)
            if local==False:
                selected=cells_array[KDTree(cells_array).query(self.cell)[1]]#return the closest cell to my point
                selected_name=''.join([str(selected[0]), '/', str(selected[1])])
                self.selected_cell.append(selected_name)
            else:
                cordis=self.choose_cell(local=True)
                centre=[cordis[0], cordis[1]] #calculate center of the square
                celda=cells_array[KDTree(cells_array).query(centre)[1]]#return the closest cell to my point
                cell_name=''.join([str(celda[0]), '/', str(celda[1])])
                return cell_name
        
    def set_dates(self):
        
        months={'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6, 'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
        meses=self.months
        yes=self.year
        years=set()
        if yes[0]=='All':
            annos=self.frame.index.get_level_values('Date').unique()
            for i in annos:
                try:
                    foo=i.year
                except AttributeError:
                    foo=parser.parse(i).year
                years.add(foo)
        elif yes[0]=='None':
            pass            
        else:
            for i in yes:
                years.add(i)
        if yes[0]=='None':
            pass
        else:
            if meses[0]=='All':
                for j in range(1,13):
                    for q in years:
                        bas=''.join([str(j), '/', str(q)])
                        self.dates.append(bas)
            elif meses[0]=='None':
                self.dates=list(years)            
            else:
                for j in meses:
                    for q in years:
                        bas=''.join([str(months[j]), '/', str(q)])
                        self.dates.append(bas)  
        
    def df_to_weibull(self):
        '''Creating a dataframe to plot weibull distribution'''
        '''Distribution is not calculated when wind speed has a float point like 1.5 or 2.5'''
        
        try:
            cell=self.selected_cell[0]
        except IndexError:
            self.select_cell()
            cell=self.selected_cell[0]
        df=self.frame.ix[cell]
        indeces=list(df.index.names)
        df_weib=pd.DataFrame(index=np.arange(0,40,0.5))
        
        if len(indeces)==1:
            devs=df.index.get_level_values(indeces[0]).unique()
            for i in devs:
                c=float(df['Wspeed1']['C'].ix[i])
                k=float(df['Wspeed1']['K'].ix[i])
                distribution=[]
                for x in np.arange(0,40,0.5):
                    prob=(k/c)*((x/c)**(k-1))*np.exp(-(x/c)**k)
                    distribution.append(prob)
                distri=pd.Series(distribution)
                df_weib[i]=distri
                
        elif len(indeces)==2:
            devs=df.index.get_level_values(indeces[0]).unique()           
            if indeces[1]=='Date':
                for i in devs:
                    for j in self.dates:
                        c=df['Wspeed1']['C'].ix[i].ix[j]
                        k=df['Wspeed1']['K'].ix[i].ix[j]
                        distribution=[]
                        for x in np.arange(0,40,0.5):
                            prob=(k / c) * ((x / c)**(k - 1)) * np.exp(-(x / c)**k)
                            distribution.append(prob)
                        distri=pd.Series(distribution)
                        joined=''.join([i, '/ ', j])
                        df_weib[joined]=distri
            elif indeces[1]=='Day/Night':
                days=df.index.get_level_values(indeces[1]).unique()
                for i in devs:
                    for j in days:
                        c=df['Wspeed1']['C'].ix[i].ix[j]
                        k=df['Wspeed1']['K'].ix[i].ix[j]
                        distribution=[]
                        for x in np.arange(0,40,0.5):
                            prob=(k / c) * ((x / c)**(k - 1)) * np.exp(-(x / c)**k)
                            distribution.append(prob)
                        distri=pd.Series(distribution)
                        joined=''.join([i, '/ ', j])
                        df_weib[joined]=distri
        
        elif len(indeces)==3:
            devs=df.index.get_level_values(indeces[0])
            days=df.index.get_level_values(indeces[2])
            for i in devs:
                for j in self.dates:
                    for k in days:
                        c=df['Wspeed1']['C'].ix[i].ix[j].ix[k]
                        k=df['Wspeed1']['K'].ix[i].ix[j].ix[k]
                        distribution=[]
                        for x in np.arange(0,40,0.5):
                            prob=(k / c) * ((x / c)**(k - 1)) * np.exp(-(x / c)**k)
                            distribution.append(prob)
                        distri=pd.Series(distribution)
                        joined=''.join([i, '/ ', j, '/ ', k])
                        df_weib[joined]=distri
        df_weib.dropna(how='all', inplace=True)
        print df_weib               
        return df_weib
            
    def df_to_charts(self):
        '''Creating a dataframe to plot bar charts with  some statistics'''
        
        try:
            cell=self.selected_cell[0]
        except IndexError:
            self.select_cell()
            cell=self.selected_cell[0]
        df=self.frame.ix[cell]
        df_temp=df['Temperature'].T
        df_press=df['Pressure'].T
        df_hum=df['Humidity'].T
        wind=df['Wspeed1'].drop(['Average', 'Roughness', 'C','K'], axis=1)
        df_wind=wind[['Hubspeed', 'Min', 'Max', 'Sdeviation']].T

        return (df_temp, df_press, df_hum, df_wind)
        
    def roses(self):
        '''Creating a dataframe to plot windrose''' #frame named raw input without indexes but with columns: cell_center, device, date, day/night
        
        indexes=list(self.frame.index.names)
        DFer=self.raw.set_index(indexes)
        try:
            cell=self.selected_cell[0]
        except IndexError:
            self.select_cell()
            cell=self.selected_cell[0]
        dfi=DFer.ix[cell]
        if self.term=='long':
            df=dfi[dfi['Wspd1']>=0]
        else:
            df=dfi[dfi['Wlifted1']>=0]
        indeces=list(df.index.names)
        
        if len(indeces)==1:
            devs=df.index.get_level_values(indeces[0]).unique()
            for i in devs:
                if self.term=='long':
                    ws=df['Wspd1'].ix[i]
                else:
                    ws=df['Wlifted1'].ix[i]
                try:
                    bas=df.ix[i].dropna(axis=1, how='all')
                    wd=bas['Wdir']
                except KeyError:
                    bas=df.ix[i].dropna(axis=1, how='all')
                    foo=list(bas.columns)
                    direc=[]
                    for item in foo:
                        if 'DIREC' in item:
                            direc.insert(0,item) #doing this the wind direction at highest altitued is taken to plot the windrose
                        else:
                            continue
                    for dire in direc:
                        try:
                            wd=bas[dire] #not necessary .ix[i] since it's already done in bas
                            break
                        except (IndexError, KeyError):
                            continue                            
                self.wros(ws, wd, dev=i)
                    
        elif len(indeces)==2:
            devs=df.index.get_level_values(indeces[0]).unique()            
            if indeces[1]=='Date':
                for i in devs:
                    for j in self.dates:
                        if self.term=='long':
                            ws=df['Wspd1'].ix[i].ix[j]
                        else:
                            ws=df['Wlifted1'].ix[i].ix[j]
                        try:
                            bas=df.ix[i].ix[j].dropna(axis=1, how='all')
                            wd=df['Wdir']
                        except KeyError:
                            bas=df.ix[i].ix[j].dropna(axis=1, how='all')
                            foo=list(bas.columns)
                            direc=[]
                            for item in foo:
                                if 'DIREC' in item:
                                    direc.insert(0,item)
                                else:
                                    continue
                            for dire in direc:
                                try:
                                    wd=bas[dire] #not necessary .ix[i] since it's already done in bas
                                    break
                                except (IndexError, KeyError):
                                    continue                            
                        self.wros(ws, wd, dev=i, date=j)
            elif indeces[1]=='Day/Night':
                days=df.index.get_level_values(indeces[1]).unique()
                for i in devs:                    
                    for j in days:
                        if self.term=='long':
                            ws=df['Wspd1'].ix[i].ix[j]
                        else:
                            ws=df['Wlifted1'].ix[i].ix[j]
                        try:
                            bas=df.ix[i].ix[j].dropna(axis=1, how='all')
                            wd=df['Wdir']
                        except KeyError:
                            bas=df.ix[i].ix[j].dropna(axis=1, how='all')
                            foo=list(bas.columns)
                            direc=[]
                            for item in foo:
                                if 'DIREC' in item:
                                    direc.insert(0,item)
                                else:
                                    continue
                            for dire in direc:
                                try:
                                    wd=bas[dire]
                                    break
                                except (IndexError, KeyError):
                                    continue                            
                        self.wros(ws, wd, dev=i, date=j)
        
        elif len(indeces)==3:
            devs=df.index.get_level_values(indeces[0]).unique()
            days=df.index.get_level_values(indeces[2]).unique()
            for i in devs:
                for j in self.dates:
                    for k in days:
                        if self.term=='long':
                            ws=df['Wspd1'].ix[i].ix[j].ix[k]
                        else:
                            ws=df['Wlifted1'].ix[i].ix[j].ix[k]
                        try:
                            bas=df.ix[i].ix[j].ix[k].dropna(axis=1, how='all')
                            wd=df['Wdir']
                        except KeyError:
                            bas=df.ix[i].ix[j].ix[k].dropna(axis=1, how='all')
                            foo=list(bas.columns)
                            direc=[]
                            for item in foo:
                                if 'DIREC' in item:
                                    direc.insert(0,item)
                                else:
                                    continue
                            for dire in direc:
                                try:
                                    wd=bas[dire]
                                    break
                                except (IndexError, KeyError):
                                    continue                            
                        self.wros(ws, wd, dev=i, date=j, base=k)

    
    def weibplot(self, dev=None, date=None, base=None):
        
        frame=self.df_to_weibull()
        shape=['-','o','s','^','--','*','+','x','.','v','p','u','H','d',',','3','>','<','4','2','1','h','_','8']
        color=['b', 'g', 'r','c','m', 'y', 'k']
        style=[''.join([a,b]) for b in shape for a in color]
        #x_axe=np.arange(0,40,0.5)
        fig=plt.figure(figsize=(20, 30), dpi=150)
        ax=fig.add_subplot(1,1,1)
        frame.plot(ax=ax, xlim=[0,50], style=style)
        ax.set_xlabel('Wind speed (m/s)')
        ax.set_ylabel('Probability')
        if self.periods==None:
            if base!=None and date!=None:
                title='Weibull curve at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' in '+str(date)+' during the '+str(base)
            elif base!=None:
                title='Weibull curve at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' during the '+str(base)
            elif date!=None:
                title='Weibull curve at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' in '+str(date)
            else:
                title='Weibull curve at '+str(self.height)+'m and at '+str(self.selected_cell[0])
        else:
            title='Weibull curve at '+str(self.height)+'m and at '+str(self.selected_cell[0])+str(self.periods)
        ax.set_title(title, fontsize=15)
        plt.show()

    def charts(self, dev=None, date=None, base=None):
        
        df_temp, df_press, df_hum, df_wind=self.df_to_charts()
        
        fig=plt.figure(figsize=(30, 40), dpi=150)
        
        ax1=fig.add_subplot(1,1,1)       
        df_temp.plot(ax=ax1, kind='bar', figsize=(15,15))
        a='Temperature (°C)'
        ax1.set_ylabel(a.decode('unicode-escape'))
        ax1.set_title('Temperature statistics at '+str(self.selected_cell[0]), fontsize=15)

        ax2=fig.add_subplot(1,1,2)
        df_press.plot(ax= ax2, kind='bar', figsize=(15,15))
        ax2.set_ylabel('Pressure (hPa)')
        ax2.set_title('Pressure statistics at '+str(self.selected_cell[0]), fontsize=15)
        
        ax3=fig.add_subplot(1,1,3)
        df_hum.plot(ax=ax3, kind='bar', figsize=(15,15))
        ax3.set_ylabel('Humidity (%)')
        ax3.set_title('Humidity statistics at '+str(self.selected_cell[0]), fontsize=15)
        
        ax4=fig.add_subplot(1,1,4)
        df_wind.plot(ax=ax4, kind='bar', figsize=(15,15))
        ax4.set_ylabel('Wind speed (m/s)')
        if self.periods==None:
            if base!=None and date!=None:
                title='Wind statistics at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' in '+str(date)+' during the '+str(base)
            elif base!=None:
                title='Wind statistics at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' during the '+str(base)
            elif date!=None:
                title='Wind statistics at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' in '+str(date)
            else:
                title='Wind statistics at '+str(self.height)+'m and at '+str(self.selected_cell[0])
        else:
            title='Wind statistics at '+str(self.height)+'m and at '+str(self.selected_cell[0])+str(self.periods)
        ax4.set_title(title, fontsize=15)
        plt.show()           

    def wros(self, ws, wd, maxi=10, dev=None, date=None, base=None):
        '''Plot a wind rose given an array of wind speed and wind direction'''

        fig = plt.figure(figsize=(30, 30), dpi=150, facecolor='w', edgecolor='w')
        rect = [0.1, 0.1, 0.8, 0.8]
        ax = WindroseAxes(fig, rect, axisbg='w')
        fig.add_axes(ax, fontsize=12)
        try:
            ax.bar(wd, ws, normed=True, opening=1, edgecolor='white',bins=[0,2,6,12,20,29,39, 50])
            ax.set_rmax(12)
            ax.set_radii_angle()
            l = ax.legend(loc=(1,0))
            if self.periods==None:
                if base!=None and date!=None:
                    title='Wind rose at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' in '+str(date)+' during the '+str(base)+' by '+str(dev)
                elif base!=None:
                    title='Wind rose at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' during the '+str(base)+' by '+str(dev)
                elif date!=None:
                    title='Wind rose at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' in '+str(date)+' by '+str(dev)
                else:
                    title='Wind rose at '+str(self.height)+'m and at '+str(self.selected_cell[0])+' by '+str(dev)
            else:
                title='Wind statistics at '+str(self.height)+'m and at '+str(self.selected_cell[0])+str(self.periods)+' by '+str(dev)
            plt.setp(l.get_texts(), fontsize=12)
            plt.title(title, fontsize=12, y=1.07)
            plt.show()
        except ValueError:
            print 'No windrose for '+str(dev)


    def get_stats(self):
        '''export data to csv file'''
            
        if os.path.exists('Output.csv'):
            for i in range(1,51):
                if os.path.exists('Output'+str(i)+'.csv'):
                    continue
                else:
                    filo='Output'+str(i)+'.csv'
                    break
        else:
            filo='Output.csv'
        self.frame.to_csv(filo)

    def reconcat(self):
        '''Concatanate again a raw frame without taking in account Devices, useful if we wanna mix insitu and satellites, not useful if we wanna compare different satellites or insitus'''

        devices=self.raw['Device'].unique()
        raws=self.raw.set_index('Device', drop=False)
        fr=[]
        for dev in devices:
            frame=raws.ix[dev].reset_index(drop=True)
            cleanning=frame.dropna(axis=1, how='all')
            clean=cleanning.sort_values(by='ID')
            fr.append(clean)
        fr2=pd.concat(fr, axis=1)
        return fr2
        
    def rough_age(self):
        
        x=self.raw['wave_age']
        y=self.raw['Roughness']
        i=np.max(x)*0.95
        j=np.max(y)*0.95
        N=len(y)
        dat=pd.DataFrame([np.array(x),np.array(y)], index=['x', 'y'])
        data=dat.T
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        data.dropna(inplace=True)
        foo=data[data['y']<1]
        datos=foo[foo['x']<50]
        xx=datos['x']
        yy=datos['y']
        fig=plt.figure(figsize=(10, 10), dpi=180)
        ax=fig.add_subplot(1,1,1)
        plt.plot(xx,yy,'o')
        ax.set_xlabel('Cp/u*')
        ax.set_ylabel('Surface roughness')
        ax.set_title('Surface roughness variability due to wave_age')
        ax.text(i, j, 'N = '+str(N), fontsize=10)
        plt.show()

    def roughcw_fric(self):
        '''plotting surface roughness produced by composition of waves against squared u*'''
        #MISSING TO INCLUDE A REGRESSION TREND LINE
        
        col=['z_cw_wave_profile_iter', 'z_cw_wave_profile_iter_+incidence', 'z_cw_wave_profile_iter_+height', 'z_cw_wave_profile_iter_complete']
        fr2=self.reconcat()
        for name in col:
            x=[x**2 for x in fr2['insitu_friction']]
            y=fr2[name]
            i=np.max(x)*0.95
            j=np.max(y)*0.95
            N=len(y)
            dat=pd.DataFrame([np.array(x),np.array(y)], index=['x', 'y'])
            data=dat.T
            data.replace([np.inf, -np.inf], np.nan, inplace=True)
            data.dropna(inplace=True)
            foo=data[data['y']<2]
            datos=foo[foo['x']<10]
            xx=datos['x']
            yy=datos['y']
            fig=plt.figure(figsize=(10, 10), dpi=180)
            ax=fig.add_subplot(1,1,1)
            plt.plot(xx,yy,'o')
            ax.set_xlabel('u*^2')
            ax.set_ylabel(name)
            ax.set_title('Zcw variability due to squared friction velocity')
            ax.text(i, j, 'N = '+str(N), fontsize=10)
            plt.show()

    def timelines(self):
        
        columns=[['iterated', 'fetch', 'log_law', 'sea_shape'], ['z_iterated', 'z_fetch', 'z_fetch_min', 'z_smith', 'z_speed', 'z_age', 'z_DTU_age', 'z_toba', 'z_log_law', 'z_wave', 'z_sea_shape']]
        title=['wind speed (m/s)', 'surface roughness']
        limits=[[0,5,10,15,25], [0,0.0001, 0.001, 0.01, 1]]
        cleanning=self.raw.dropna(axis=1, how='all')
        clean=cleanning.sort_values(by='ID')
        for i in title:
            data=clean[columns[title.index(i)]]
            limit=limits[title.index(i)]
            fig=plt.figure(figsize=(10, 10), dpi=180)
            a=0
            while a<len(limit)-1:
                foo=data[data>limit[a]]
                datos=foo[foo<limit[a+1]].dropna(how='all')
                ax=fig.add_subplot(2,2,a+1)
                if a+1==3 or a+1==4:
                    ax.set_xlabel('Measurements')
                else:
                    pass
                if a+1==1 or a+1==3:
                    ax.set_ylabel(i)
                else:
                    pass
                ax.plot(datos)
                a+=1
            fig.suptitle('Comparison of methodologies for '+i)
            plt.show()

    def regression(self, parameter):
        '''parameter is the list of columns under comparison'''        
                 
        if parameter=='wspeed':
            if 'toba' and 'smith' and 'fetch' in self.raw.columns:
                columns=['iterated', 'fetch', 'fetch_min', 'smith', 'speed', 'age', 'DTU_age', 'toba', 'log_law', 'wave', 'sea_shape', 'fetch_iter','speed_iter', 'wave_iter', 'sea_shape_iter', 'wave_profile_iter', 'otterman_iter', 'wave_profile', 'otterman', 'Wlifted1']
            else:
                columns=['Wlifted1']
            title=['Wind speed (m/s)']
        elif parameter=='roughness':
            if 'toba' and 'smith' and 'fetch' in self.raw.columns:
                columns=['z_iterated', 'z_fetch', 'z_fetch_min', 'z_smith', 'z_speed', 'z_age', 'z_DTU_age', 'z_toba', 'z_log_law', 'z_wave', 'z_sea_shape', 'z_fetch_iter','z_speed_iter', 'z_wave_iter', 'z_sea_shape_iter', 'z_wave_profile_iter', 'z_otterman_iter', 'z_wave_profile', 'z_otterman', 'z_rabaneda', 'Roughness']
            else:
                columns=['z01', 'Roughness']
            title=['Surface roughness']
        elif parameter=='friction':
            columns=['u*1', 'insitu_friction']
            title=['Friction velocity (m/s)']
        elif parameter=='drag':
            columns=['Cd1', 'Cd_insitu']
            title=['Neutral drag coefficient at 10 m (x1000)']
        elif parameter=='all':
            columns=[['iterated', 'fetch', 'fetch_min', 'smith', 'speed', 'age', 'DTU_age', 'toba', 'log_law', 'wave', 'sea_shape', 'fetch_iter','speed_iter', 'wave_iter', 'sea_shape_iter', 'wave_profile_iter', 'otterman_iter', 'wave_profile', 'wave_profile_iter_+incidence', 'wave_profile_iter_+height', 'wave_profile_iter_complete', 'otterman', 'wave_profile_+incidence', 'wave_profile_+height', 'wave_profile_+gustiness', 'wave_profile_G_incidence', 'wave_profile_complete', 'wind_wave_profile', 'wind_wave_profile_+incidence', 'wind_wave_profile_+height', 'wind_wave_profile_complete', 'wind_wave_profile_gustiness', 'full_insitu', 'Wlifted1'], ['z_iterated', 'z_fetch', 'z_fetch_min', 'z_smith', 'z_speed', 'z_age', 'z_DTU_age', 'z_toba', 'z_log_law', 'z_wave', 'z_sea_shape', 'z_fetch_iter','z_speed_iter', 'z_wave_iter', 'z_sea_shape_iter', 'z_wave_profile_iter', 'z_wave_profile_iter_+incidence', 'z_wave_profile_iter_+height', 'z_wave_profile_iter_complete', 'z_otterman_iter', 'z_wave_profile', 'z_wave_profile_+incidence', 'z_wave_profile_+height', 'z_wave_profile_+gustiness', 'z_wave_profile_G_incidence', 'z_wave_profile_complete', 'z_wind_wave_profile', 'z_wind_wave_profile_+incidence', 'z_wind_wave_profile_+height', 'z_wind_wave_profile_complete', 'z_wind_wave_profile_gustiness', 'z_otterman', 'z_full_insitu', 'z_rabaneda', 'Roughness'], ['Cd1', 'Cd_insitu'], ['u*1', 'insitu_friction', 'u*_iterated', 'u*_fetch_iter', 'u*_speed_iter', 'u*_wave_iter', 'u*_sea_shape_iter', 'u*_wave_profile_iter', 'u*_wave_profile_iter_+incidence', 'u*_wave_profile_iter_+height', 'u*_wave_profile_iter_complete', 'u*_otterman_iter', 'u*_full_insitu']]
            title=['Wind speed (m/s)', 'Surface roughness', 'Neutral drag coefficient at 10 m (x1000)', 'Friction velocity (m/s)']
            
        
        ref=raw_input('Select the reference device for regression: ')
        devices=self.raw['Device'].unique()
        while ref in devices:
            break
        else:
            ref=raw_input('Wrong answer, Select the reference device: ')
        nulls=raw_input('Do you want to remove points over the axis?(y/n): ')
        if nulls!='y' and nulls!='n':
            nulls='y'
        else:
            pass
        raws=self.raw.set_index('Device', drop=False)
        
        for i in range(len(title)):
            X_data=[]
            Y_data=[]
            for dev in devices:
                frame=raws.ix[dev].reset_index(drop=True)
                cleanning=frame.dropna(axis=1, how='all')
                clean=cleanning.sort_values(by='ID')
                for col in columns[i]:
                    try:
                        if dev==ref:
                            X=clean[col]
                            xim=(X, dev)
                            X_data.append(xim)
                        else:
                            Y=clean[col]
                            combo=(Y, ''+dev+' + '+col+' method')
                            Y_data.append(combo)
                    except KeyError:
                        continue
            print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Plotting regression >>>>>'
            for mix in Y_data:
                self.linear(X_data[0][0], mix[0], X_data[0][1], mix[1], title[i], remove_null=nulls)
                    
    def linear(self, x, y , x_name, y_name, title, remove_null='n'):

        dat=pd.DataFrame([np.array(x),np.array(y)], index=['x', 'y'])
        data=dat.T
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        if remove_null=='y':
            if title=='Wind speed (m/s)':
                datos=data[data>0.009].dropna()
                decims=3
            elif title=='Surface roughness':
                datos=data[data['x']<0.02]#THIS ALSO ELIMINATES NAN and inf
                frame=datos[datos['y']<0.02]
                decims=12
            else:
                datos=data[data>0.00001].dropna()
                frame=datos.dropna()
                decims=3

        elif remove_null=='n':
            frame=data.dropna()
        xx=frame['x']
        yy=frame['y']
        '''Something wrong here, too much difference between removed and non-removed regression, like the points are mixed. Not sure but I think is actually solved'''
        if title=='Wind speed (m/s)':
            decims=3
        elif title=='Surface roughness':
            decims=12
        else:
            decims=3
        fig=plt.figure(figsize=(10, 10), dpi=180)
        ax=fig.add_subplot(1,1,1)
        try:
            N=len(yy)
            s_value, i_value, r_value, p_value, std_err = stats.linregress(xx, yy)
            p1=[s_value, i_value]
            slope=np.round(p1[0], decimals=decims)
            intercep=np.round(p1[1], decimals=decims)
            nrmse=(np.float(sum(yy-xx)**2)/np.float(sum(xx**2)))**0.5
            s_value, i_value, r_value, p_value, std_err = stats.linregress(xx, yy)
            r2=np.round(r_value**2, decimals=8)
            bias=np.average(yy)-np.average(xx)
            plt.plot(xx,yy,'o')
            plt.plot(xx, np.polyval(p1,xx), 'r-')
        except ZeroDivisionError:
            pass
        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        ax.set_title(title)
        
        if title=='Wind speed (m/s)':
            axes=plt.gca()
            minim=0
            maxim=35
            axes.set_xlim([minim,maxim])
            axes.set_ylim([minim,maxim])
            i=maxim*0.05
            j=(maxim-(maxim*0.25))
            x=range(minim, maxim+1, 1)
            plt.plot(x, x, 'k-')
        elif title=='Surface roughness':
            axes=plt.gca()
            minim=0
            maxim=2.5
            maxim_x=2.5
            axes.set_xlim([minim,maxim_x])
            axes.set_ylim([minim,maxim])
            i=maxim_x*0.05
            j=(maxim-(maxim*0.25))
        elif title=='Neutral drag coefficient at 10 m (x1000)':
            axes=plt.gca()
            minim=0
            maxim=int(np.amax([np.amax(xx), np.amax(yy)]))
            maxim_x=maxim
            axes.set_xlim([minim,maxim_x])
            axes.set_ylim([minim,maxim])
            i=maxim_x*0.05
            j=(maxim-(maxim*0.25))
            x=range(minim, maxim+1, 1)
            plt.plot(x, x, 'k-')
        elif title=='Friction velocity (m/s)':
            axes=plt.gca()
            minim=0
            maxim=2
            axes.set_xlim([minim,maxim])
            axes.set_ylim([minim,maxim])
            i=maxim*0.05
            j=(maxim-(maxim*0.25))
            x=range(minim, maxim+1, 1)
            plt.plot(x, x, 'k-')
        else:
            pass
        try:
            ax.text(i, j, 'N = '+str(N)+'\nR squared = '+str(r2)+'\ny = '+str(slope)+'x + '+str(intercep)+'\nNRMSE = '+str(nrmse)+'\nBias = '+str(bias), fontsize=10)
            plt.show()
        except UnboundLocalError:
            print 'No regression for '+str(x_name)
            
    def export(self):
        
        '''Exporting csv file to use with WASP, use instant basis'''
        
        import sys
        from Commons import timestamp
        
        #to know where hddc's are
        mean=np.average(list(self.frame['Wspeed1']['Samples']))
        frame1=self.frame[self.frame['Wspeed1']['Samples'] > mean]
        hddcs=frame1.index.get_level_values('cell_center').unique()
        
        #filter rawframe according devices
        frame2=self.raw.set_index('Device')
        devices=frame2.index.unique()
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Exporting HDDCs data>>>>>'
        print 'Devices available: ' +str(devices)
        print '\nWhat satellites would you like to remove: (None to select all)'
        leng=len(devices)
        a=0
        satellites=[]
        while a < len(devices)+1:
            a+=1
            sates=raw_input('Satellite : ')
            if sates=='None' or sates=='':
                break
            elif not sates in devices:
                print 'Wrong satellite name'
                continue
            else:
                satellites.append(sates)
        if leng==0:
            sys.exit('No satellites included')
        frame31=frame2.drop(satellites)
        frame3=timestamp(frame31)
        
        #filter frame3 according to each hddc separately and export it
        frame3.reset_index(inplace=True)
        frame3.set_index('cell_center', inplace=True)
        filepath=raw_input('Full, absolute path to fold where to export:')
        for cell in hddcs:
            time=frame3.ix[cell]['Timestamp']
            speed=frame3.ix[cell]['Wlifted1']
            direction=frame3.ix[cell]['Wdir']
            frame4=pd.DataFrame()
            frame4[0], frame4[1], frame4[2]=time, speed, direction
            #filtering wspeed and wdirection
            frame4[frame4[1] < 0] =np.nan
            frame4[frame4[2] < 0] = np.nan
            frame4[frame4[2] > 360] = np.nan
            frame4.dropna(inplace=True)
            frame4.set_index(0, inplace=True)
            frame4.sort_index(inplace=True)
            frame4.reset_index(inplace=True)
            cell2=cell.replace('/', '_')
            path=''.join([filepath, '/', cell2,'.csv'])
            frame4.to_csv(path, index=False)
            
            
        
        
        
        
        
        
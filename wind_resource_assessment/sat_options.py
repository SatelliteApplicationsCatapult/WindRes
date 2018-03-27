# -*- coding: utf-8 -*-
"""
Created on Wed Nov 04 16:57:05 2015

@author: Alberto S. Rabaneda
"""
from Extraction import FromDB
from read_sat import Sat_csv
import sys
import os
from options import Insitu_options
from sat_processing import Merging, Lifting, Sat_calcs, Prepare_sat
import pandas as pd
from outputs import Plotting
from mapping import Wind_map
from datetime import datetime
import numpy as np
import Commons

class Satellite_options:
    
    #all following varables are class varables and therefore static variables, move to __init__() adding self. to convert to instance variables
    coord=object()
    inst=object()
    satellits=set()
    rain=object()
    winds=object()
    path=object()
    plots=set()
    years=[]
    months=[]
    base=object()
    union=object()
    periodic=None

    def sat_data(self):
    
        sat=raw_input('Would you like to use satellite data? (y/n):')
        if sat=='n':
            self.execution0()
        elif sat=='y':
            source=raw_input('From local file or extract from DB? (file/DB):')           
            if source=='DB':
                self.execution()
                FromDB(self.coord, self.path)
                self.execution2()
            elif source=='file':
                grid=raw_input('Would you like to reuse already gridded data? (y/n): ')
                filters=raw_input('Would you like to reuse shifted data by same parameters? (y/n): ')# This is to have an option to work with the calculated dataframe without doing smae calculations again
                if grid=='n':
                    self.execution2()
                elif grid=='y' and filters=='n':
                    self.execution2(grid=True)
                elif grid=='y' and filters=='y':
                    self.execution3()
                else:
                    sys.exit('Wrong answer, start again')
            else:
                sys.exit('Wrong answer, start again')
        else:
            sys.exit('Wrong answer, start again')

    def set_place(self):    
        
        print'\nSet area:'
        lon1=input('\tLongitude 1 (-180 to 180):')
        lon2=input('\tLongitude 2 (-180 to 180):')
        lat1=input('\tLatitude 1 (-90 to 90):')
        lat2=input('\tLatitude 2 (-90 to 90):')
        try:
            loni1 = float(lon1)+180
            loni2 = float(lon2)+180
            lati1 = float(lat1)+90
            lati2 = float(lat2)+90
            self.coord=(loni1, loni2, lati1, lati2)
        except ValueError:
            sys.exit('One coordenate is not a number, Try again!')
            
    def satellites(self):
        
        foo=raw_input('Would you like to select satellites by name or by instrument? (name/instrument): ')
        if foo=='name':
            self.satell()
        elif foo=='instrument':
            self.set_instru()
        else:
            sys.exit('Wrong answer, start again')
        
        ree=raw_input('Would you like to process all satellites together? (y/n): ')
        if ree!='y' and ree!='n':
            sys.exit('Wrong answer, start again')
        else:
            self.union=ree
                
    def set_instru(self):
        #default value is All
        
        Instru=['Radiometers', 'Scatterometers', 'SARs', 'rad-scatt', 'scatt-SAR', 'rad-SAR', 'All']
        print '\nInstrument options: '+str(Instru)
        self.inst=raw_input('\nWhat kind of instruments would you like to include:')
        if not self.inst in Instru:
            self.inst='All'
                
    def satell(self):
        #no default value
        
        Sats=['All', 'Windsat', 'Quikscat', 'ASCAT', 'OSCAT', 'Rapidscat', 'Sentinel1', 'SSMIf08', 'SSMIf10', 'SSMIf11', 'SSMIf13', 'TMI', 'AMSR2', 'AMSRE']
        print '\nSatellites availables: '+str(Sats)
        print '\nWhat satellites would you like to include:'        
        a=0
        while a<20:
            a+=1
            sates=raw_input('Satellite '+str(a)+': ')
            if sates=='All':
                self.satellits.add('All')
                break
            elif sates=='':
                break
            elif not sates in Sats:
                print 'Wrong satellite name'
                continue
            else:
                self.satellits.add(sates)
        if len(self.satellits)==0:
            sys.exit('No satellites included')
            
    def rain_rate(self):
        #default value is 0 mm/hr
        
        self.rain=input('\nChoose limit for rain rate (mm/hr): ')
        try:
            float(self.rain)
        except ValueError:
            print 'Not a number, rain rate is 0'
            self.rain=0        
    
    def wind_study(self):
        
        self.winds=raw_input('Wind measurements to consider (only_main, all): ')
        if self.winds!='all':
            self.winds='only_main'
        
    def filedirec(self):
        
        try:
            self.path=raw_input('\nWrite full, absolute path to folder to keep data from db: ')
            if os.path.isdir(self.path)==False:
                sys.exit('Folder does not exisit')
        except SyntaxError:
            sys.exit('Wrong path')
            
    def set_outplots(self):
        
        plotis=['Weibull_curve', 'Charts', 'Wind_rose', 'Parameters', 'Wind map', 'Regression', 'Export', 'Timelines', 'Z_wave_age', 'Zcw_friction', 'All']
        print '\nSelect outputs: ' +str(plotis)        
        a=0
        while a<6:
            a+=1
            foo=raw_input('Output: ')
            if foo=='All':
                self.plots.add('All')
                break
            elif foo=='':
                break
            elif not foo in plotis:
                print 'Wrong output'
                continue
            else:
                self.plots.add(foo)
        if len(self.plots)==0:
            print 'No output selected, "Parameters" chosen'
            self.plots.add('Parameters')
            
    def set_period(self):
        '''Set period, for both date and time'''
        
        dateopt=raw_input('\nDo you want to include date interval?(y/n)')
        if dateopt=='y':
            first=raw_input('Starting date (dd/mm/yyyy):')
            last=raw_input('End date (dd/mm/yyyy):')
            start=datetime.strptime(first, '%d/%m/%Y').date()
            end=datetime.strptime(last, '%d/%m/%Y').date()
        else:
            start=None
            end=None
        timeopt=raw_input('\nDo you want to include time interval?(y/n)')
        if timeopt=='y':
            earl=raw_input('Starting time (hh:mm:ss):')
            lat=raw_input('Finishing time (hh:mm:ss):')
            early=datetime.strptime(earl, '%H:%M:%S').time()
            late=datetime.strptime(lat, '%H:%M:%S').time()
        else:
            early=None
            late=None
        self.periodic=[start, end, early, late]
        
    def set_months(self):
        #default value is None
        
        months=['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'All', 'None']
        print '\nWhat months would you like to include: '+str(months)        
        a=0
        while a<11:
            a+=1
            mes=raw_input('Month '+str(a)+': ')
            if mes=='All':
                self.months.append('All')
                break
            elif mes=='None':
                self.months.append('None')
                break
            elif mes=='':
                break
            elif not mes in months:
                print 'Wrong month name'
                pass
            else:
                if not mes in self.months:
                    self.months.append(mes)
                else:
                    continue
        if len(self.months)==0:
            print 'No month selected'
            self.months.append('None')
            
    def set_years(self):
        #default value is None
        
        print '\nWhat year/s would you like to include (All to select all, None to unselect all): '        
        a=0
        while a<20:
            a+=1
            anno=raw_input('Year '+str(a)+': ')
            if anno=='All':
                self.years.append('All')
                break
            elif anno=='None':
                self.years.append('None')
                break
            elif anno=='':
                break
            else:
                if not anno in self.years:
                    self.years.append(anno)
                else:
                    continue
        if len(self.years)==0:
            sys.exit('No year selected')
            
    def set_basis(self):
        
        selection=['day', 'night', 'All', 'None']        
        print '\nWhat day basis would you like to choose? '+str(selection)
        foo=raw_input('Day basis: ')
        if not foo in selection:
            print 'No basis selected, "None" chosen'
            self.base='None'
        else:
            self.base=foo
            
    def join_dfs(self, dfs):
        '''This concatenate all df's of list dfs'''
        
        try:
            dfs2=[]
            for x in dfs:
                x.set_index('ID', inplace=True)
                dfs2.append(x)
        except KeyError:
            dfs2=dfs       
        if len(dfs2)>1:
            frame=pd.concat(dfs2)
        else:
            frame=dfs2[0]
        try:
            frame.reset_index(inplace=True)
        except ValueError:
            pass
        return frame
        
    def showing(self, df, raw, months, years, heig, term, per):
        
        bas=Plotting(df, raw, months, years, heig, term, per)
        if 'Weibull_curve' in self.plots:           
            bas.weibplot()
        else:
            pass
        if 'Wind_rose' in self.plots:
            bas.roses()
        else:
            pass
        if 'Charts' in self.plots:
            bas.charts()
        else:
            pass
        if 'Parameters' in self.plots:
            bas.get_stats()
        else:
            pass
        if 'Export' in self.plots:
            bas.export()
        else:
            pass
        if 'Wind map' in self.plots:
            try:
                self.coord[0]
            except TypeError:
                self.set_place()
            mmap=Wind_map(df, self.coord, heig)
            mmap.execution()
        else:
            pass
        variables=['wspeed', 'roughness', 'friction', 'drag', 'all']
        if 'Regression' in self.plots:
            par=raw_input('Select paramaters to do regression '+str(variables)+': ')
            while not par in variables:
                print 'Wrong option. Try again'
                par=raw_input('Select paramaters to do regression '+str(variables)+': ')
            bas.regression(parameter=par)
        else:
            pass
        if 'Z_wave_age' in self.plots:
            bas.rough_age()
        else:
            pass
        if 'Zcw_friction' in self.plots:
            bas.roughcw_fric()
        else:
            pass
        if 'Timelines' in self.plots:
            bas.timelines()
        else:
            pass
        if 'All' in self.plots: 
            mmap=Wind_map(df, self.coord, heig)
            mmap.execution()
            bas.weibplot()
            bas.roses()
            bas.charts()
            bas.get_stats()
            par=raw_input('Select paramaters to do regression '+str(variables)+': ')
            while not par in variables:
                print 'Wrong option. Try again'
                par=raw_input('Select paramaters to do regression '+str(variables)+': ')
            bas.regression(parameter=par)
            bas.rough_age()
            bas.roughcw_fric()
            bas.timelines()
            bas.export()                      
        else:
            pass
            
    def execution0(self):
        '''Execution when no satellite data is selected'''
        
        insitu=Insitu_options(coords=None)
        insitu.execution()
                
    def execution(self):
        '''Execution to extract data from database'''
        
        self.set_place()
        self.filedirec()
    
    def execution2(self, grid=False):
        '''Execution to process satellite data & insitu data if chosen'''
        
        if grid is False:
            self.satellites()
            self.rain_rate()
            self.wind_study()
            st1=Sat_csv(self.satellits, self.inst, self.rain, self.winds, self.union)
            stream=st1.filtering()
            try:
                self.coord[0]
            except (IndexError, TypeError):
                self.set_place()
            st2=Merging(self.satellits, self.coord, stream)
            stream2=st2.select_cell()
            filepath=raw_input('Full, absolute path to csv file to keep filtered dataframe:')
            stream2.to_csv(filepath)
            del stream
        elif grid is True:
            filepath=raw_input('Full, absolute path to file with applied grid: ')
            df=pd.read_csv(filepath, low_memory=False, chunksize=100000, iterator=True)
            stream=pd.concat(df, ignore_index=True)
            stream.replace('\N', np.nan, inplace=True)
            try:
                stream['Date']=[datetime.strptime(x, '%Y-%m-%d') for x in stream['Date']]
            except ValueError:
                stream['Date']=[datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in stream['Date']]
            try:
                stream['Time']=[datetime.strptime(x, '%H:%M:%S') for x in stream['Time']]
            except ValueError:
                try:
                    stream['Time']=[datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in stream['Time']]
                except ValueError:
                    stream['Time']=[datetime.strptime(x[:-6], '%Y-%m-%d %H:%M:%S') for x in stream['Time']]
            stream2=stream
            del stream
            try:
                self.coord[0]
            except (IndexError, TypeError):
                self.set_place()
        
        stream2=Commons.timestamp(stream2)
        stream2=Commons.inver_dir(stream2)          
        height=input('Select hub height for satellite data (m): ')
        term=raw_input('\nDo you want to calculate with long-term or instant basis?(long/instant): ')
        print '\nWhat methodology want to use for surface roughness and friction velocity?'
        methodology=['iteration', 'fetch', 'fetch_min', 'smith', 'toba', 'speed', 'age', 'dtu_age', 'log_law', 'wave', 'rabaneda', 'experimental', 'all', 'ac_sensitivity', 'cw_sensitivity', 'expo_sensitivity']
        method=raw_input(str(methodology)+': ')
        if method in methodology:
            method=method
        else:
            method=raw_input('Wrong name, repeat '+ str(methodology) +': ')
        st3=Prepare_sat(stream2)
        stream3=st3.execution()
        if method=='iteration' or method=='fetch':
            st35=Lifting(height, stream3, term=term, how=method)
            stream35=st35.execution()        
            filepath=raw_input('Full, absolute path to csv file to keep filtered dataframe:')
            stream35.to_csv(filepath)
        else:
            stream35=stream3
        periodically=raw_input('Would you like to set period?(y/n)')
        if periodically=='y':
            self.set_period()
        self.set_years()
        self.set_months()
        self.set_basis()
        mix=raw_input('Would you like to include in-situ measurements?(y/n)')
        if mix=='y' or method!='iteration' or method!='fetch':        
            insitu=Insitu_options(self.coord, dia=self.base, mes=self.months, anno=self.years, satellites=self.satellits, term=term, periodic=self.periodic, sat_frame=stream35)
            Dframe, direcdf, sat_df=insitu.execution_sat()
            if isinstance(sat_df, pd.DataFrame):
                stream35=sat_df
            else:
                pass
            if method!='iteration' or method!='fetch':
                st37=Lifting(height, stream35, term=term, how=method, insitu=direcdf)
                stream37=st37.execution()
                filepath=raw_input('Full, absolute path to csv file to keep filtered dataframe:')
                stream37.to_csv(filepath)
            else:
                stream37=stream35
            st4=Sat_calcs(self.base, self.months, self.years, stream37, height, term=term, period=self.periodic)
            stream4=st4.execution()
            lis=[stream4, Dframe]
            zas=[stream37, direcdf]
            raw=self.join_dfs(zas)
            frame=self.join_dfs(lis)
            self.set_outplots()
            self.showing(frame, raw, self.months, self.years, height, term, self.periodic)
        else:
            st4=Sat_calcs(self.base, self.months, self.years, stream37, height, term=term, period=self.periodic)
            stream4=st4.execution()      
            self.set_outplots()
            self.showing(stream4, stream37, self.months, self.years, height, term, self.periodic)
        
    def execution3(self):
        '''Execution to select already filtered satellite data, and process it with insitu data if chosen'''
        
        filepath=raw_input('Full, absolute path to file with applied filters: ')
        df=pd.read_csv(filepath, low_memory=False, chunksize=100000, iterator=True)
        stream=pd.concat(df, ignore_index=True)
        stream.replace('\N', np.nan, inplace=True)
        try:
            stream['Date']=[datetime.strptime(x, '%Y-%m-%d') for x in stream['Date']]
        except ValueError:
            stream['Date']=[datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in stream['Date']]
        try:
            stream['Time']=[datetime.strptime(x, '%H:%M:%S') for x in stream['Time']]
        except ValueError:
            try:
                stream['Time']=[datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in stream['Time']]
            except ValueError:
                stream['Time']=[datetime.strptime(x[:-6], '%Y-%m-%d %H:%M:%S') for x in stream['Time']]
        height=input('At what height had the winds been lifted?(m): ')
        term=raw_input('\nWhat basis was chosen long-term or instant basis?(long/instant): ')
        try:
            self.coord[0]
        except (IndexError, TypeError):
            self.set_place()
        stream=Commons.timestamp(stream)
        stream=Commons.inver_dir(stream)
        periodically=raw_input('Would you like to set period?(y/n)')
        if periodically=='y':
            self.set_period()
        self.set_years()
        self.set_months()
        self.set_basis()
        mix=raw_input('Would you like to include in-situ measurements?(y/n)')
        if mix=='y':
            insitu=Insitu_options(self.coord,dia=self.base, mes=self.months, anno=self.years, satellites=self.satellits, term=term, periodic=self.periodic, sat_frame=stream)
            Dframe, direcdf, sat_df=insitu.execution_sat()
            if isinstance(sat_df, pd.DataFrame):
                stream=sat_df
            else:
                pass
            st2=Sat_calcs(self.base, self.months, self.years, stream, height, term=term, period=self.periodic)
            stream2=st2.execution()
            lis=[stream2, Dframe]
            zas=[stream, direcdf]
            raw=self.join_dfs(zas)
            frame=self.join_dfs(lis)
            self.set_outplots()
            self.showing(frame, raw, self.months, self.years, height, term, self.periodic)
        else:
            st2=Sat_calcs(self.base, self.months, self.years, stream, height, term=term, period=self.periodic)
            stream2=st2.execution()      
            self.set_outplots()
            self.showing(stream2, stream, self.months, self.years, height, term, self.periodic)

#--------------------------------------------------------------------------------------------------------------------
       
if __name__=='__main__':

    sat=Satellite_options()
    sat.sat_data()
                  
    

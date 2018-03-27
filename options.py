# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 12:32:19 2015

@author: Alberto
"""
import sys
from read_insitu import Read_excel, Insitu_calcs, Overlapping 
from outputs import Plotting
import pandas as pd
from create_template import create_template
from datetime import datetime
import numpy as np
import Commons

class Insitu_options:
    
    def __init__(self, coords, dia=None, mes=None, anno=None, satellites=None, term='long', periodic=None, sat_frame=None):
        
        self.netfiles=[]
        if anno!=None:
            self.years=anno
        else:
            self.years=[]
        if dia!=None:
            self.base=dia
        else:
            self.base=object()
        self.plots=set()
        self.stream=object()
        if mes!=None:
            self.months=mes
        else:
            self.months=[]
        self.filtered=[]
        self.indeces=object()
        self.sats=satellites
        self.coords=coords
        self.term=term
        if periodic!=None:
            self.periodic=periodic
        else:
            self.periodic=None
        self.sat_frame=sat_frame
    
    def templates(self):
        
        plates=raw_input('Do you need to create templates? (y/n): ')
        if plates=='y':
            create_template()
        else:
            pass
    
    def select_files(self):
        
        filters=raw_input('Would you like to reuse filtered data? (y/n): ')# This is to have an option to work with the calculated dataframe without doing smae calculations again
        if filters=='y':
            a=0
            while a<51:
                a+=1
                item=raw_input('Select full, absolute path to filtered file ' +str(a)+': ')
                if item!='':
                    self.filtered.append(item)
                else:
                    break
        else:
            print 'Files to study: '
            for x in range(1,51):
                file1=raw_input('\tFile '+str(x)+': ')
                if file1!='':
                    self.netfiles.append(file1)
                else:
                    break
        
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
                print 'Wrong satellite name'
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
            
    def set_stability(self):
        
        sta=raw_input('\nOnly neutral stability:(y/n)')
        if sta=='y':
            neutral=True
        else:
            neutral=False
        return neutral

    def set_period(self):
        '''Set period, for both date and time'''
        
        dateopt=raw_input('\nDo you want to include date interval?(y/n)')
        if dateopt=='y':
            start=raw_input('Starting date (dd/mm/yyyy):')
            end=raw_input('End date (dd/mm/yyyy):')
        else:
            start=None
            end=None
        timeopt=raw_input('\nDo you want to include time interval?(y/n)')
        if timeopt=='y':
            early=raw_input('Starting time (hh:mm:ss):')
            late=raw_input('Finishing time (hh:mm:ss):')
        else:
            early=None
            late=None
        self.periodic=[start, end, early, late]
            
    def set_outplots(self):
        
        plotis=['Weibull_curve', 'Charts', 'Wind_rose', 'Parameters', 'Wind map', 'All']
        print '\nSelect outputs: ' +str(plotis)        
        a=0
        while a<5:
            a+=1
            foo=raw_input('Output: ')
            if foo=='All':
                self.plots.add('All')
                break
            elif foo=='':
                break
            elif not foo in plotis:
                print 'Wrong output'
                pass
            else:
                self.plots.add(foo)
        if len(self.plots)==0:
            print 'No output selected, "Parameters" chosen'
            self.plots.add('Parameters')
            
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
        
    def wave_filter(self, frame):
        
        if 'SIGNIFICANT_WAVE(m)' in frame.columns:
            maxi=input('Set maximum wave height (m):')
            mini=input('Set minimum wave height (m):')
            frame1=frame[frame['SIGNIFICANT_WAVE(m)']<maxi]
            frame2=frame1[frame1['SIGNIFICANT_WAVE(m)']>mini]
            return frame2
        else:
            pass
        
    def wave_age_filter(self, frame):
        
        if 'wave_age' in frame.columns:
            maxi=input('Set maximum wave age:')
            mini=input('Set minimum wave age:')
            frame=frame[frame['insitu_friction']>0]
            frame1=frame[frame['wave_age'].astype(float)<maxi]
            frame2=frame1[frame1['wave_age'].astype(float)>mini]
            return frame2
        else:
            pass
        
    def wspeed_filter(self, frame):
        
        if 'Wlifted1' in frame.columns:
            maxi=input('Set maximum wind speed:')
            mini=input('Set minimum wind speed:')
            frame=frame[frame['insitu_friction']>0]
            frame1=frame[frame['Wlifted1'].astype(float)<maxi]
            frame2=frame1[frame1['Wlifted1'].astype(float)>mini]
            return frame2
        else:
            pass
                
    def showing(self, df, raw, heig, per, term, miss=None):
        
        bas=Plotting(df, raw, self.months, self.years, heig, period=per, term=term)
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
        if 'Wind map' in self.plots:
            sys.exit('No satellite data')
        else:
            pass
        if 'All' in self.plots:
            bas.weibplot()
            bas.roses()
            bas.charts()
            bas.get_stats()
        else:
            pass
            
    def execution(self):
        
        DFs=[]
        raws=[]
        self.templates()
        self.select_files()
        periodically=raw_input('Would you like to set period?(y/n)')
        if periodically=='y':
            self.set_period()
        self.set_years()
        self.set_months()
        self.set_basis()      
        if len(self.filtered)!=0:
            term=raw_input('\nWhat basis was chosen long-term or instant basis?(long/instant): ')
            hei=input('At which height had the winds been lifted?(m): ')
            for item in self.filtered:
                df=pd.read_csv(item, low_memory=False, chunksize=100000, iterator=True)
                stream=pd.concat(df, ignore_index=True)
                stream.replace('\N', np.nan, inplace=True)
                stream['Date']=[datetime.strptime(x, '%Y-%m-%d') for x in stream['Date']]
                stream['Time']=[datetime.strptime(x, '%H:%M:%S') for x in stream['Time']]
                raws.append(stream)
                stream=Commons.timestamp(stream)
                stream=self.wave_filter(stream)
                stre2=Insitu_calcs(self.base, self.months, self.years, stream, term=term, period=self.periodic)
                stream2=stre2.execution()
                DFs.append(stream2)
        else:
            term=raw_input('\nDo you want to calculate with long-term or instant basis?(long/instant): ')
            coordinates=None            
            for item in self.netfiles:
                stre=Read_excel(coordinates, item, self.sats, term=term, neutral=self.set_stability())
                stream, hei=stre.execution()
                raws.append(stream)
                stream=Commons.timestamp(stream)
                stream=self.wave_filter(stream)
                stre2=Insitu_calcs(self.base, self.months, self.years, stream, term=term, period=self.periodic)
                stream2=stre2.execution()
                DFs.append(stream2)
        raw=self.join_dfs(raws)
        frame=self.join_dfs(DFs)
        self.set_outplots()
        self.showing(frame, raw, hei, self.periodic, term=term)
        
    def execution_sat(self):
        '''#OVERLAPPING IT'S ONLY WORKING WHEN I USE ONLY ONE INSITU DEVICE'''
        
        DFs=[]
        raws=[]
        self.templates()
        self.select_files()
        if len(self.filtered)!=0:
            #hei=input('At which height had the winds been lifted?(m): ')
            for item in self.filtered:
                df=pd.read_csv(item, low_memory=False, chunksize=1000000, iterator=True)
                stream=pd.concat(df, ignore_index=True)
                try:
                    stream['Date']=[datetime.strptime(x, '%Y-%m-%d') for x in stream['Date']]
                    stream['Time']=[datetime.strptime(x, '%H:%M:%S') for x in stream['Time']]
                except ValueError:
                    stream['Date']=[datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in stream['Date']]
                    stream['Time']=[datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in stream['Time']]
                stream=Commons.timestamp(stream)
                stream=self.wave_filter(stream)
                stream=self.wave_age_filter(stream)
                stream=self.wspeed_filter(stream)
                if self.periodic != None:
                    overlapping=raw_input('Do you want to use insitu data only when it overlaps with satellite data?(y/n): ')
                else:
                    overlapping='n'
                if overlapping=='y':
                    over=Overlapping(self.sat_frame, stream, self.periodic, self.coords)
                    stream, sat_df=over.execution()
                else:
                    sat_df=None
                    pass
                raws.append(stream)
                stre2=Insitu_calcs(self.base, self.months, self.years, stream, term=self.term, period=self.periodic)
                stream2=stre2.execution()
                DFs.append(stream2)
        else:
            for item in self.netfiles:
                stre=Read_excel(self.coords, item, self.sats, term=self.term, neutral=self.set_stability())
                stream, hei=stre.execution()
                stream=Commons.timestamp(stream)
                stream=self.wave_filter(stream)
                #stream=self.wave_age_filter(stream)
                #stream=self.wspeed_filter(stream)
                if self.periodic != None:
                    overlapping=raw_input('Do you want to use insitu data only when it overlaps with satellite data?(y/n): ')
                else:
                    overlapping='n'
                if overlapping=='y':
                    over=Overlapping(self.sat_frame, stream, self.periodic, self.coords)
                    stream, sat_df=over.execution()
                else:
                    sat_df=None
                    pass
                raws.append(stream)
                stre2=Insitu_calcs(self.base, self.months, self.years, stream, term=self.term, period=self.periodic)
                stream2=stre2.execution()
                DFs.append(stream2)
        direcdf=self.join_dfs(raws)
        direcdf.to_csv('Egmond_overlapped_25.csv')
        Dframe=self.join_dfs(DFs)
        return Dframe, direcdf, sat_df
        
        

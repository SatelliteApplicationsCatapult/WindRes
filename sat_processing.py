# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 16:41:53 2015

@author: ftb14219
"""
import numpy as np
#from scipy.spatial import KDTree
from pandas import DataFrame
import pandas as pd
import dateutil.parser as parser
from scipy import special
import datetime
import sys
import itertools
import math

class Merging:
    
    def __init__(self, satellites, coordenates, dataframe):
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting grid >>>'
        self.satellites=satellites
        self.coord =coordenates
        if self.coord==None:
            self.set_place()
        self.dataframe=dataframe
        
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
            
    def set_resol(self):
        '''set the grid of maximum resolution depending on the chosen satellites'''
        
        if 'Sentinel1' or 'All' or 'SARs' or 'scatt-SAR' or 'rad-SAR' in self.satellites:
            resol=0.02
        elif 'Rapidscat' in self.satellites:
            resol=0.16
        else:
            resol=0.25
        return resol
        
    def set_grid(self):
        '''calculate the center of each cell of the grid and return all their coordinates as an array'''
        
        step=self.set_resol()
        a=self.coord[0]+(step/2)
        b=self.coord[1]
        c=self.coord[2]+(step/2)
        d=self.coord[3]        
        cells_center=[]
        for i in np.arange(a, b, step):
            for j in np.arange(c, d, step):
                cells_center.append([i,j])
        cells=np.array(cells_center)
        return cells
        
    def select_cell(self):
        '''Read each row of my dataframe and insert it into a new dataframe with cell center as index'''
        '''BE CAREFUL IT COULD MOVE SAR REAL GRID!!!!'''
        
        '''This method is the bottle neck!!!!!!!!!!!!!!!!'''
        
        cells_array=self.set_grid()
        #cell_list=[]
        #for i, row in self.dataframe.iterrows():
         #   centre=[(row['Long1']+row['Long2'])/2, (row['Lat1']+row['Lat2'])/2]
          #  celda=cells_array[KDTree(cells_array).query(centre)[1]]#return the closest cell to my point
           # cell=[celda[0]-180, celda[1]-90]
            #cell_name=''.join([str(cell[0]), '/', str(cell[1])])
            #cell_list.append(cell_name)
        #self.dataframe['cell_center']=cell_list#add a column with name of cells for each row'''
        g=self.gen_cell(cells_array)
        self.dataframe['cell_center']=list(g)
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Grid has been set >>>'        
        return self.dataframe
    
    def gen_centre(self, long1_array, long2_array, lat1_array, lat2_array):
        
        for long1, long2, lat1, lat2 in itertools.izip(long1_array, long2_array, lat1_array, lat2_array):
            centre=[(long1+long2)/2, (lat1+lat2)/2]
            yield centre
        
        
    def gen_cell(self, cells_array):
        '''return the closest cell to my point '''
        
        cent=self.gen_centre(self.dataframe['Long1'], self.dataframe['Long2'], self.dataframe['Lat1'], self.dataframe['Lat2'])
        centres=list(cent)
        for centre in centres:
            foo=self.gen_dist(centre, cells_array)
            distances=list(foo)
            mini=min(distances)
            celda=cells_array[distances.index(mini)]
            #celda=cells_array[KDTree(cells_array).query(centre)[1]]#return the closest cell to my point           
            cell=[celda[0]-180, celda[1]-90]
            cell_name=''.join([str(cell[0]), '/', str(cell[1])])
            yield cell_name
            
    def gen_dist(self, point, cells_array):
        '''cells_array is an array [[x1,y1], [x2,y2],...]'''
        '''point is [x,y]'''
        
        for i in cells_array:
            dist=np.sqrt(((point[0]-i[0])**2)+((point[1]-i[1])**2))
            yield dist


class Lifting:
    '''This class takes a dataframe, and adds the columns for friction velocity
    surface roughness, and wind velocity at selected height'''   
    
    def __init__(self, height, dataframe, term='long', how='iteration', insitu=None):
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Lifting wind speed >>>'
        self.height=float(height)
        try:
            self.df=dataframe.sort_values(by='ID')
        except KeyError:
            self.df=dataframe.sort_values(by='Timestamp')
        self.term=term
        self.reference=object
        self.how=how
        self.insitu=insitu
        #the next is to allow this class to be used for insitu dataframes as extrapolation methods
        if 'Wspd1' in self.df.columns:
            self.one='Wspd1'
            self.two='Wspd2'
            self.three='Wspd3'
        elif 'WIND SPEED10(m/s)' in self.df.columns:
            self.one='WIND SPEED10(m/s)'
        else:
            print 'Wind has been measured at too high altitude to be extrapolated through the use of friction velocity'''
        #next is the common code to run in case it is necessary insitu data to shift satellite wind speed
        if insitu is not None:
            self.joint2=self.joint()
        else:
            pass
    
    def float_indexing(self, array):
        '''When I need to index using a float number, I always convert to string since I can have problems working with floats.
        But for some numbers I still have problems, like 8.00 or 7.80 because it's represented as 8 instead of 8.00, this method is to solve this'''        
        
        for x in array:
            if not '.' in x:
                x=x+'.00'
            elif x[-2]=='.':
                x=x+'0'
            else:
                x=x
            yield x

    def friction_vel(self):
        '''Selection of friction velocity calculation method'''

        frictions=['Edson', 'Wu', 'Maat', 'Toba', 'Insitu']
        way=raw_input('Choose method for friction velocity calculation: '+str(frictions)+' :')
        if way=='Edson':
            self.friction()
        elif way=='Wu':
            self.friction_wu()
        elif way=='Maat' and self.how!='fetch':
            self.friction_maat()
        elif way=='Toba' and self.how!='fetch':
            self.friction_toba()
        elif way=='Maat' or way=='Toba' and self.how=='fetch':
            sys.exit('Missing insitu data, use fet_min method to use Maat friction method')
        elif way=='Insitu':
            self.friction_insitu()
        
    
    def execution(self):
        
        if self.how=='all':
            self.k_viscosity()
            #iterated
            f=pd.read_csv('Refer.csv', dtype={'uz':str})
            G=self.float_indexing(f['uz'])
            f['uz']=list(G)
            foo=f.set_index('uz')
            self.reference=foo
            self.iterated()
            self.lifted('iterated')
            self.df['z_iterated']=self.df['z01']
            self.df['u*_iterated']=self.df['u*1']
            
            #wave_profile simple
            self.iterations(mode='shape', Lettau=True, profile=1)
            self.z_cw('z_cw_wave_profile_iter')
            self.lifted('wave_profile_iter')
            self.df['z_wave_profile_iter']=self.df['z01']
            self.df['u*_wave_profile_iter']=self.df['u*1']
            #wave_profile incidence
            self.iterations(mode='shape', Lettau=True, profile=2)
            self.z_cw('z_cw_wave_profile_iter_+incidence')
            self.lifted('wave_profile_iter_+incidence')
            self.df['z_wave_profile_iter_+incidence']=self.df['z01']
            self.df['u*_wave_profile_iter_+incidence']=self.df['u*1']
            #wave_profile height correction
            self.iterations(mode='shape', Lettau=True, profile=3)
            self.z_cw('z_cw_wave_profile_iter_+height')
            self.lifted('wave_profile_iter_+height')
            self.df['z_wave_profile_iter_+height']=self.df['z01']
            self.df['u*_wave_profile_iter_+height']=self.df['u*1']
            #wave_profile complete
            self.iterations(mode='shape', Lettau=True, profile=4)
            self.z_cw('z_cw_wave_profile_iter_complete')
            self.lifted('wave_profile_iter_complete')
            self.df['z_wave_profile_iter_complete']=self.df['z01']
            self.df['u*_wave_profile_iter_complete']=self.df['u*1']
            #otterman
            self.iterations(mode='shape', Lettau=False)
            self.lifted('otterman_iter')
            self.df['z_otterman_iter']=self.df['z01']
            self.df['u*_otterman_iter']=self.df['u*1']
            #fetch_iter
            self.fetch()
            self.iterations()
            self.lifted('fetch_iter')
            self.df['z_fetch_iter']=self.df['z01']
            self.df['u*_fetch_iter']=self.df['u*1']
            #speed_iter
            self.charnock_speed()
            self.iterations()
            self.lifted('speed_iter')
            self.df['z_speed_iter']=self.df['z01']
            self.df['u*_speed_iter']=self.df['u*1']
            #wave_iter
            self.charnock_wave_slope()
            self.iterations()
            self.lifted('wave_iter')
            self.df['z_wave_iter']=self.df['z01']
            self.df['u*_wave_iter']=self.df['u*1']
            #sea_shape_iter
            self.air_sea(mode='sea_shape', mode2=False, itera=True)
            self.Z_friction()
            self.lifted('sea_shape_iter')
            self.df['z_sea_shape_iter']=self.df['z01']
            self.df['u*_sea_shape_iter']=self.df['u*1']
                                    
            self.friction_vel()
            
            #fetch
            self.fetch()
            self.charnock_roughness(insitu=False)
            self.lifted('wave_profile')
            self.df['z_wave_profile']=self.df['z01']           
            #fetch_min
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
            self.lifted('fetch_min')
            self.df['z_fetch_min']=self.df['z01']
            #smith
            self.charnock_smith()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
            self.lifted('smith')  
            self.df['z_smith']=self.df['z01']
            #speed
            self.charnock_speed()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
            self.lifted('speed')
            self.df['z_speed']=self.df['z01']
            #age
            self.charnock_wave_age()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
            self.lifted('age')
            self.df['z_age']=self.df['z01']
            #DTU_age
            self.fetch(mode='age')
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
            self.lifted('DTU_age')
            self.df['z_DTU_age']=self.df['z01']
            #Toba
            self.charnock_toba()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
            self.lifted('toba')
            self.df['z_toba']=self.df['z01']
            #log_law
            self.roughness_log_law()
            self.lifted('log_law')
            self.df['z_log_law']=self.df['z01']
            #wave
            self.air_sea()
            self.lifted('wave')
            self.df['z_wave']=self.df['z01']
            #sea_shape
            self.air_sea(mode='sea_shape', mode2=False)
            self.lifted('sea_shape')
            self.df['z_sea_shape']=self.df['z01']
            #rabaneda
            self.z0_wave_profile(profile=7)
            self.df['z_rabaneda']=self.df['z01']
            
        elif self.how=='iteration':
            #Merette's method
            f=pd.read_csv('Refer.csv', dtype={'uz':str})
            G=self.float_indexing(f['uz'])
            f['uz']=list(G)
            foo=f.set_index('uz')
            self.reference=foo
            self.iterated()
        elif self.how=='fetch':
            #DTU method for roughness
            self.friction_vel()
            self.fetch()
            self.charnock_roughness(insitu=False)
        elif self.how=='fetch_min':
            #DTU method for roughness but applying minimum roughness according z0 vs u*
            self.friction_vel()
            self.k_viscosity()
            self.fetch()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
        elif self.how=='smith':
            #Charnock according to Smith
            self.friction_vel()
            self.k_viscosity()
            self.charnock_smith()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
        elif self.how=='speed':
            #Charnock according to U10, Edson
            self.friction_vel()
            self.k_viscosity()
            self.charnock_speed()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
        elif self.how=='age':
            #Charnock according to wave_age, Edson
            self.friction_vel()
            self.k_viscosity()
            self.charnock_wave_age()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
        elif self.how=='dtu_age':
            #Chranock according to DTU but without changing wave_age for fetch
            self.friction_vel()
            self.k_viscosity()
            self.fetch(mode='age')
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
        elif self.how=='toba':
            #Charnock according to Toba
            self.friction_vel()
            self.k_viscosity()
            self.charnock_toba()
            self.charnock_roughness()
            self.min_z0(list(self.df['kinematic']), charnock=list(self.df['charnock']), mode='fetch')
        elif self.how=='log_law':
            #Roughness calculated through drag and log_law, but including wave_age, wave_height, U10, gustiness, relative_speed
            self.friction_vel()
            self.roughness_log_law()
        elif self.how=='sea_shape' or self.how=='wave':
            #Roughness according to wave_slope, Edson(wave) or Taylor(sea_state)
            self.friction_vel()
            self.k_viscosity()
            self.air_sea()
        elif self.how=='rabaneda':
            self.friction_vel()
            self.k_viscosity()
            self.z0_wave_profile(profile=7)
        elif self.how=='experimental':
            #this is for testing surface roughness methods
            self.friction_vel()
            self.k_viscosity()
            #wave_profile simple
            self.z0_wave_profile(profile=1)
            self.lifted('wave_profile')
            self.df['z_wave_profile']=self.df['z01']
            self.df['u*_wave_profile']=self.df['u*1']
            #wave_profile incidence
            self.z0_wave_profile(profile=2)
            self.lifted('wave_profile_+incidence')
            self.df['z_wave_profile_+incidence']=self.df['z01']
            self.df['u*_wave_profile_+incidence']=self.df['u*1']
            #wave_profile height correction
            self.z0_wave_profile(profile=3)
            self.lifted('wave_profile_+height')
            self.df['z_wave_profile_+height']=self.df['z01']
            self.df['u*_wave_profile_+height']=self.df['u*1']
            #wave_profile gustiness
            self.z0_wave_profile(profile=4)
            self.lifted('wave_profile_+gustiness')
            self.df['z_wave_profile_+gustiness']=self.df['z01']
            self.df['u*_wave_profile_+gustiness']=self.df['u*1']
            #wave_profile gustiness and incidence
            self.z0_wave_profile(profile=5)
            self.lifted('wave_profile_G_incidence')
            self.df['z_wave_profile_G_incidence']=self.df['z01']
            self.df['u*_wave_profile_G_incidence']=self.df['u*1']
            #wave_profile complete
            self.z0_wave_profile(profile=6)
            self.lifted('wave_profile_complete')
            self.df['z_wave_profile_complete']=self.df['z01']
            self.df['u*_wave_profile_complete']=self.df['u*1']
            #extrapolation for insitu u* and z0
            self.df['u*1']=self.joint2['insitu_friction']
            self.df['z01']=self.joint2['Roughness']
            self.lifted('full_insitu')
            self.df['z_full_insitu']=self.df['z01']
            self.df['u*_full_insitu']=self.df['u*1']
            #wind_wave_profile simple
            self.z0_wave_profile_iter('b_wind_wave_profile', profile=1)
            self.lifted('wind_wave_profile')
            self.df['z_wind_wave_profile']=self.df['z01']
            self.df['u*_wind_wave_profile']=self.df['u*1']
            #wind_wave_profile incidence
            self.z0_wave_profile_iter('b_wind_wave_profile_+incidence', profile=2)
            self.lifted('wind_wave_profile_+incidence')
            self.df['z_wind_wave_profile_+incidence']=self.df['z01']
            self.df['u*_wind_wave_profile_+incidence']=self.df['u*1']
            #wind_wave_profile height correction
            self.z0_wave_profile_iter('b_wind_wave_profile_+height', profile=3)
            self.lifted('wind_wave_profile_+height')
            self.df['z_wind_wave_profile_+height']=self.df['z01']
            self.df['u*_wind_wave_profile_+height']=self.df['u*1']
            #wind_wave_profile complete
            self.z0_wave_profile_iter('b_wind_wave_profile_complete', profile=4)
            self.lifted('wind_wave_profile_complete')
            self.df['z_wind_wave_profile_complete']=self.df['z01']
            self.df['u*_wind_wave_profile_complete']=self.df['u*1']
            #wind_wave_profile gustiness
            self.z0_wave_profile_iter('b_wind_wave_profile_gustiness', profile=5)
            self.lifted('wind_wave_profile_gustiness')
            self.df['z_wind_wave_profile_gustiness']=self.df['z01']
            self.df['u*_wind_wave_profile_gustiness']=self.df['u*1']
        elif self.how=='ac_sensitivity':
            #sensitivity analysis on ac
            self.friction_vel()
            self.k_viscosity()
            pro={1:'wave_profile', 2:'wave_profile_+incidence', 3:'wave_profile_+height', 4:'wave_profile_+gustiness', 5:'wave_profile_G_incidence', 6:'wave_profile_complete'}
            for i in range(1, 7, 1):
                for j in np.arange(0.5, 2.1, 0.1):
                    self.z0_wave_profile(profile=i, ac_coef=j)
                    self.lifted(pro[i]+'_ac_coef:'+str(j))
                    self.df['z_'+pro[i]+'_ac_coef:'+str(j)]=self.df['z01']
        elif self.how=='cw_sensitivity':
            #sensitivity analysis on composition of waves effect
            self.friction_vel()
            self.k_viscosity()
            pro={1:'wave_profile', 2:'wave_profile_+incidence', 3:'wave_profile_+height', 4:'wave_profile_+gustiness', 5:'wave_profile_G_incidence', 6:'wave_profile_complete'}
            for j in np.arange(60, 82, 2):
                self.z0_wave_profile(profile=2, alpha_wc=j)
                self.lifted(pro[2]+'_cw_coef:'+str(j))
                self.df['z_'+pro[2]+'_cw_coef:'+str(j)]=self.df['z01']
        elif self.how=='expo_sensitivity':
            #sensitivity analysis on composition of waves effect
            self.friction_vel()
            self.k_viscosity()
            pro={1:'wave_profile', 2:'wave_profile_+incidence', 3:'wave_profile_+height', 4:'wave_profile_+gustiness', 5:'wave_profile_G_incidence', 6:'wave_profile_complete'}

            for j in np.arange(2, 3.05, 0.05):
                self.z0_wave_profile(profile=2, alpha_wc=34, expo=j)
                self.lifted(pro[2]+'_cw_coef:'+str(j))
                self.df['z_'+pro[2]+'_cw_coef:'+str(j)]=self.df['z01']                    
                
        else:
            print '\nNo method for extrapolation selected'
        if self.how!='all' and self.how!='ac_sensitivity':   
            self.lifted(self.how)
            self.drag()
        else:
            pass
        return self.df
    
    def joint(self):
        
        try:
            self.df.reset_index(inplace=True)
        except ValueError:
            self.df.reset_index(drop=True, inplace=True)
        try:
            self.insitu.reset_index(inplace=True)
        except ValueError:
            self.insitu.reset_index(drop=True, inplace=True)
        try:
            sats=self.df.sort_values(by='ID')
            insitu=self.insitu.sort_values(by='ID')
        except KeyError:
            sats=self.df.sort_values(by='Timestamp')
            insitu=self.insitu.sort_values(by='Timestamp')
        insi=insitu[['TEMPERATURE(C)', 'PRESSURE(hPa)', 'HUMIDITY(%)', 'SIGNIFICANT_WAVE(m)', 'Phase_speed', 'Gustiness', 'Wave_direction', 'WAVELENGHT(m)','WAVEPERIOD(s)', 'TSEA(C)', 'VERTICAL_SPEED(m/s)', 'HORIZONTAL_SPEED(m/s)', 'insitu_friction','MEAN_HEIGHT(m)', 'Roughness', 'U10']]
        joint2=pd.concat([sats, insi], axis=1)
        #joint2=joint.T.drop_duplicates().T #This will allow me to use this method between insitu measurements too
        return joint2
    
    def friction_maat(self):
        '''Calculating friction velocity as function of cp and Hs. For the algorithm it was considered wave age and wave height'''
        
        if self.term=='long':
            pass
            #long-term plus different devices overcomplicate calculations and it is more ralistic to work on instant basis or averages for a short period (hours)
            
        elif self.term=='instant':
            #I'm adding a 0.001 to avoid division by zero. This will not change results since sensibility in wind measurements is 0.01
            
            self.df['u*1']=((9.81**2)*(self.joint2['SIGNIFICANT_WAVE(m)'])**2)/((1.04**2)*(self.joint2['Phase_speed']**3))
            if 'Wspd2' in self.df.columns:            
                self.df['u*2']=list(self.df['u*1'])
            else:
                self.df['u*2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['u*3']=list(self.df['u*1'])
            else:
                self.df['u*3']=np.nan
                
    def friction_toba(self):
        '''To calculate friction velocity as function of period and significant wave height'''

        if self.term=='long':
            pass
        elif self.term=='instant':
            self.df['u*1']=(((self.joint2['SIGNIFICANT_WAVE(m)'])**2)/(0.362404*9.81*((self.joint2['WAVEPERIOD(s)'])**2)))
            if 'Wspd2' in self.df.columns:            
                self.df['u*2']=list(self.df['u*1'])
            else:
                self.df['u*2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['u*3']=list(self.df['u*1'])
            else:
                self.df['u*3']=np.nan
        
    
    def friction_insitu(self):
        '''This will choose friction velocity calculated according to vertical and horizontal velocities'''
        
        self.df['u*1']=list(self.joint2['insitu_friction'])
        if 'Wspd2' in self.df.columns:            
            self.df['u*2']=list(self.joint2['insitu_friction'])
        else:
            self.df['u*2']=np.nan
        if 'Wspd3' in self.df.columns:
            self.df['u*3']=list(self.joint2['insitu_friction'])
        else:
            self.df['u*3']=np.nan
 
    def Z_friction(self):
        '''Calculations for friction velocity according to surface roughness and neutral wind speed at 10m'''
        
        #Drag coefficient=(1.03*10**-3+((0.04*10**-3)*(U)**1.48))/(U)**0.21
        #friction**2= Drag coefficient*(U**2)
        
        if self.term=='long':
            
            devices=self.df['Device'].unique()
            frame=self.df.set_index('Device', drop=True)
            one={}
            two={}
            three={}
            for dev in devices:
                x=np.average(frame.ix[dev][self.one])
                y=np.average(frame.ix[dev]['z01'])
                one[dev]=(x*0.4)/(np.log(10/y))
                if 'Wspd2' in self.df.columns:
                    x=np.average(frame.ix[dev][self.two])
                    y=np.average(frame.ix[dev]['z02'])
                    two[dev]=(x*0.4)/(np.log(10/y))
                else:
                    two[dev]=np.nan
                if 'Wspd3' in self.df.columns:
                    x=np.average(frame.ix[dev][self.three])
                    y=np.average(frame.ix[dev]['z03'])
                    three[dev]=(x*0.4)/(np.log(10/y))
                else:
                    three[dev]=np.nan
            self.df.set_index('Device', inplace=True)
            self.df['u*1']=pd.Series(one)
            self.df['u*2']=pd.Series(two)
            self.df['u*3']=pd.Series(three)
            self.df.reset_index(inplace=True)
            
        elif self.term=='instant':
            #I'm adding a 0.001 to avoid division by zero. This will not change results since sensibility in wind measurements is 0.01
            
            self.df['u*1']=(self.df[self.one]*0.4)/(np.log(10/self.df['z01']))
            if 'Wspd2' in self.df.columns:            
                self.df['u*2']=(self.df[self.one]*0.4)/(np.log(10/self.df['z02']))
            else:
                self.df['u*2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['u*3']=(self.df[self.one]*0.4)/(np.log(10/self.df['z03']))
            else:
                self.df['u*3']=np.nan
   
    def friction_wu(self):
        '''Calculations for friction velocity according to drag coefficient and neutral wind speed at 10m'''
        
        #Drag coefficient=(1.03*10**-3+((0.04*10**-3)*(U)**1.48))/(U)**0.21
        #friction**2= Drag coefficient*(U**2)
        
        if self.term=='long':
            
            devices=self.df['Device'].unique()
            frame=self.df.set_index('Device', drop=True)
            one={}
            two={}
            three={}
            for dev in devices:
                x=np.average(frame.ix[dev][self.one])
                one[dev]=np.sqrt((x**2)*(0.8+((0.065)*(x)))*10**-3)
                if 'Wspd2' in self.df.columns:
                    x=np.average(frame.ix[dev][self.two])
                    two[dev]=np.sqrt((x**2)*(0.8+((0.065)*(x)))*10**-3)
                else:
                    two[dev]=np.nan
                if 'Wspd3' in self.df.columns:
                    x=np.average(frame.ix[dev][self.three])
                    three[dev]=np.sqrt((x**2)*(0.8+((0.065)*(x)))*10**-3)
                else:
                    three[dev]=np.nan
            self.df.set_index('Device', inplace=True)
            self.df['u*1']=pd.Series(one)
            self.df['u*2']=pd.Series(two)
            self.df['u*3']=pd.Series(three)
            self.df.reset_index(inplace=True)
            
        elif self.term=='instant':
            #I'm adding a 0.001 to avoid division by zero. This will not change results since sensibility in wind measurements is 0.01
            
            self.df['u*1']=np.sqrt((self.df[self.one]**2)*(0.8+((0.065)*(self.df[self.one])))*10**-3)
            if 'Wspd2' in self.df.columns:            
                self.df['u*2']=np.sqrt((self.df[self.one]**2)*(0.8+((0.065)*(self.df[self.one])))*10**-3)
            else:
                self.df['u*2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['u*3']=np.sqrt((self.df[self.one]**2)*(0.8+((0.065)*(self.df[self.one])))*10**-3)
            else:
                self.df['u*3']=np.nan
                
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Friction velocity calculated >>>'
        
    def friction(self):
        '''Calculations for friction velocity according to drag coefficient and neutral wind speed at 10m'''
        
        #Drag coefficient=(1.03*10**-3+((0.04*10**-3)*(U)**1.48))/(U)**0.21
        #friction**2= Drag coefficient*(U**2)
        
        if self.term=='long':
            
            devices=self.df['Device'].unique()
            frame=self.df.set_index('Device', drop=True)
            one={}
            two={}
            three={}
            for dev in devices:
                x=np.average(frame.ix[dev][self.one])
                one[dev]=np.sqrt((x**2)*((1.03*10**-3+((0.04*10**-3)*(x)**1.48))/(x)**0.21))
                if 'Wspd2' in self.df.columns:
                    x=np.average(frame.ix[dev][self.two])
                    two[dev]=np.sqrt((x**2)*((1.03*10**-3+((0.04*10**-3)*(x)**1.48))/(x)**0.21))
                else:
                    two[dev]=np.nan
                if 'Wspd3' in self.df.columns:
                    x=np.average(frame.ix[dev][self.three])
                    three[dev]=np.sqrt((x**2)*((1.03*10**-3+((0.04*10**-3)*(x)**1.48))/(x)**0.21))
                else:
                    three[dev]=np.nan
            self.df.set_index('Device', inplace=True)
            self.df['u*1']=pd.Series(one)
            self.df['u*2']=pd.Series(two)
            self.df['u*3']=pd.Series(three)
            self.df.reset_index(inplace=True)
            
        elif self.term=='instant':
            #I'm adding a 0.001 to avoid division by zero. This will not change results since sensibility in wind measurements is 0.01
            
            self.df['u*1']=np.sqrt((self.df[self.one]**2)*((1.03*10**-3+((0.04*10**-3)*(self.df[self.one])**1.48))/(self.df[self.one] + 0.001)**0.21))
            if 'Wspd2' in self.df.columns:            
                self.df['u*2']=np.sqrt((self.df[self.two]**2)*((1.03*10**-3+((0.04*10**-3)*(self.df[self.two])**1.48))/(self.df[self.two] + 0.001)**0.21))
            else:
                self.df['u*2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['u*3']=np.sqrt((self.df[self.three]**2)*((1.03*10**-3+((0.04*10**-3)*(self.df[self.three])**1.48))/(self.df[self.three] + 0.001)**0.21))
            else:
                self.df['u*3']=np.nan
                
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Friction velocity calculated >>>'
            
    def fetch(self, mode='distance'):
        '''Calculating roughness according to fetch, i.e. distance to shore'''
               
        if mode=='distance':   
            filepath=raw_input('Full, absolute path to file with radial distance to shore: ')
            dist_frame=pd.read_csv(filepath)
            dist_frame.set_index('Direction', inplace=True)
            dist=np.amin(dist_frame['Fetch(km)'])
            if 'Wdir' in self.df.columns:
                fetch=[]
                for direc in self.df['Wdir'].astype(float):                
                    if np.isnan(direc):
                        fetch.append(dist)
                    else:
                        for i in range(10, 370, 10):
                            if direc<=i:
                                var=dist_frame.ix[i]['Fetch(km)']
                                fetch.append(var)
                                break                       
                            else:
                                continue
                self.df['Fetch']=fetch
            else:
                self.df['Fetch']=dist
            self.df['w_age1']=(3.5/2*np.pi)*(((self.df[self.one]**2)/(self.df['Fetch']*9.81))**(1./3))
        elif mode=='age':
            self.df['w_age1']=self.df['u*1']/self.joint2['Phase_speed']
        self.df['charnock']=((1.89*self.df['w_age1']**1.59))/(1+(47.165*self.df['w_age1']**2.59)+(11.791*self.df['w_age1']**4.59))
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Roughness calculated >>>'
 
    def charnock_smith(self):
        
        self.df['charnock']=0.48*(self.df['u*1']/self.joint2['Phase_speed'])
        
    def charnock_toba(self):
        
        self.df['charnock']=0.025*(self.df['u*1']/self.joint2['Phase_speed'])
        
    def charnock_speed(self):
        
        self.df['charnock']=(0.017*self.df[self.one])-0.005
        
    def charnock_wave_age(self):
        
        self.df['charnock']=0.114*(self.df['u*1']/self.joint2['Phase_speed'])**0.622
        
    def charnock_wave_slope(self):
        
        self.df['charnock']=(2*np.pi*0.09*self.joint2['SIGNIFICANT_WAVE(m)'])/self.joint2['WAVELENGHT(m)']
        
    def charnock_roughness(self, insitu=True):
        '''This method is to calculate rouhgness when rough regime is based in Charnock parameter'''
        
        if insitu is True:
            self.joint2['smooth']=0.11*(self.joint2['kinematic']/self.df['u*1'])
            self.joint2['trans']=0.1*((self.joint2['kinematic']*self.df['u*1']/9.81)**0.5)
            self.joint2['rough']=self.df['charnock']*(self.df['u*1']**2)/9.81
            g=self.z_regim2(list(self.joint2['kinematic'].astype(float)), list(self.df['charnock'].astype(float)), list(self.df['u*1'].astype(float)), list(self.joint2['smooth'].astype(float)), list(self.joint2['trans'].astype(float)), list(self.joint2['rough'].astype(float)))
            self.df['z01']=list(g)
        elif insitu is False:
            self.df['z01']=self.df['charnock']*(self.df['u*1']**2)/9.81 
            
        if 'Wspd2' in self.df.columns:
            self.df['z02']=self.df['charnock']*(self.df['u*2']**2)/9.81 
        else:
            self.df['z02']=np.nan
        if 'Wspd3' in self.df.columns:
            self.df['z03']=self.df['charnock']*(self.df['u*3']**2)/9.81
        else:
            self.df['z03']=np.nan
                
    def drift_speed(self, T, L, ac, wsp, wd, wave_dir):
        
        u0=(4*np.pi*ac**2)/(T*L)
        wind_east=wsp*np.sin(wd*(2*np.pi/360.))
        wind_north=wsp*np.cos(wd*(2*np.pi/360.))
        wave_east=u0*np.sin(wd*(2*np.pi/360.))
        wave_north=u0*np.cos(wd*(2*np.pi/360.))
        ur=(((wind_east-wave_east)**2)+((wind_north-wave_north)**2))**(1./2)
        return ur
    
    def iterations(self, mode='charnock', Lettau=True, profile=1):
        
        if mode=='charnock':
            g=self.gen_charnock_iterations(self.df['Wspd1'], self.df['charnock'])
        elif mode=='shape':
            g=self.gen_wave_profile_iterations(self.joint2['SIGNIFICANT_WAVE(m)'], self.joint2['WAVEPERIOD(s)'], self.joint2['WAVELENGHT(m)'],self.joint2['U10'], self.df['Wdir'], self.joint2['Wave_direction'], self.df['kinematic'], Lettau=Lettau, profile=profile)
        mix=pd.DataFrame(list(g), columns=['r', 'f'])
        self.df['z01'], self.df['u*1']=mix['r'], mix['f']
        del mix
        
            
    def gen_charnock_iterations(self, wsp, cha):
        '''Knowing the charnock parameter and wind speed at 10m , this method calculates z0 and friction velocity through log_law and charnock's equation'''
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Starting iterations >>>'
        zipped=zip(wsp, cha)
        for zipi in zipped:
            wspeed=str("%.2f"%zipi[0])
            char=zipi[1]
            for i in np.arange(0.000001, 6, 0.00000001, dtype=np.float32):#using a precision of 0.0001 in friction velocity we have a precision of 0.01 in wind speed
                z0=((i**2)*char)/9.81
                u1=(np.log(10/z0))*(i/0.4)
                u=str("%.2f"%u1)
                if u==wspeed:
                    roughness=z0
                    fric=i
                    yield (roughness, fric)
                    break
                else:
                    continue
                
            
    def gen_wave_profile_iterations(self, H, T, L, wsp, wd, wave_dir, v, Lettau=True, profile=1):
        '''Calculates the highest point of the wave crest in relation with SWL'''
        #bad iteration method, u* compensation
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Starting iterations >>>'
        zipi=zip(H, T, L, wsp, wd, wave_dir, v)
        q=1
        for zz in zipi:
            foo=zz[0]/(9.81*zz[1]**2)
            k=2*np.pi/zz[2]
            E=k*zz[0]/2
            wspeed=str("%.2f"%zz[3])
            if zz[0]/zz[2]>(1/7.):
                ac=np.nan
                roughness=np.nan
                fric=np.nan
                yield (roughness, fric)
            else:
                if foo<=0.001:
                    ac=zz[0]/2.
                elif foo>0.001 and foo<0.0075:
                    ac=(zz[0]/2.)+(0.5*E**2)
                elif foo>=0.0075:
                    ac=(zz[0]/2.)+(0.5*E**2)+((2/3.)*E**4)
                ur=self.drift_speed(zz[1], zz[2], ac, zz[3], zz[4], zz[5])   
                for i in reversed(np.arange(0.00000001, 6, 0.00000001, dtype=np.float32)):#using a precision of 0.0001 in friction velocity we have a precision of 0.01 in wind speed
                    inci=zz[4]-zz[5]                    
                    if Lettau==True:
                        if profile==1:
                            z0=(((i/zz[3])**(1/0.41))*zz[2]*(1+(zz[0]/(zz[0]-ac))))+(0.11*zz[6]/i)
                        elif profile==2:
                            z0=60*((i/zz[3])**(2.35))
                        elif profile==3:
                            z0=((i**2)*((ac*np.exp(-zz[0]/zz[2]))**2)/((ur**2)*zz[2]))+(0.11*zz[6]/i)
                        elif profile==4:
                            z0=(((i**2)*((ac*np.exp(-zz[0]/zz[2]))**2)/((ur**2)*zz[2]))*np.absolute(math.cos(math.radians(inci))))+(0.11*zz[6]/i)
                    elif Lettau==False:
                        z0=(i**2)*(ac**2)*(1-np.e**(-1*ac/zz[2]))/(ur**2)
                    u1=(np.log(10/z0))*(i/0.4)
                    u=str("%.2f"%u1)
                    if u==wspeed:
                        roughness=z0
                        fric=i
                        print q
                        q+=1
                        yield (roughness, fric)
                        break
                    else:
                        if i==0.00000001:
                            print 'not found'
                            roughness=np.nan
                            fric=np.nan
                            yield (roughness, fric)
                        else:
                            continue
                    
    def z0_wave_profile(self, profile=1, ac_coef=1, alpha_wc=0, expo=2.35):
        '''Calculates the highest point of the wave crest in relation with SWL'''
        #insitu u* method
        
        zipi=zip(self.joint2['SIGNIFICANT_WAVE(m)'], self.joint2['WAVEPERIOD(s)'], self.joint2['WAVELENGHT(m)'],self.joint2['U10'], self.df['Wdir'], self.joint2['Wave_direction'], self.df['kinematic'], self.df['u*1'], self.joint2['Gustiness'], self.joint2['Roughness'])
        #(0:H, 1:T, 2:L, 3:wsp, 4:wd, 5:wave_dir, 6:v, 7:fric, 8:G, 9:insi_rough)
        roughis=[]
        coeff=[]
        coeff2=[]
        aces=[]
        for zz in zipi:
            #alpha_wc=zz[2]
            foo=zz[0]/(9.81*zz[1]**2)
            k=2*np.pi/zz[2]
            E=k*zz[0]/2
            if zz[0]/zz[2]>(1/7.):
                z0=np.nan
            else:
                if foo<=0.001:
                    ac=(zz[0]/2.)*ac_coef
                    if ac>zz[0]:
                        ac=zz[0]# ac cannot be higher than wave height
                    else:
                        ac=ac
                elif foo>0.001 and foo<0.0075:
                    ac=((zz[0]/2.)+(0.5*E**2))*ac_coef
                    if ac>zz[0]:
                        ac=zz[0]# ac cannot be higher than wave height
                    else:
                        ac=ac
                elif foo>=0.0075:
                    ac=((zz[0]/2.)+(0.5*E**2)+((2/3.)*E**4))*ac_coef
                    if ac>zz[0]:
                        ac=zz[0]# ac cannot be higher than wave height
                    else:
                        ac=ac
                aces.append(ac)
                ur=self.drift_speed(zz[1], zz[2], ac, zz[3], zz[4], zz[5])
                inci=np.absolute(math.radians(zz[4])- math.radians(zz[5]))                    
                if profile==1:#simple
                    z0=(((zz[7]**2)/(ur**2))*(((ac**2)/zz[2])+alpha_wc))+(0.11*zz[6]/zz[7])
                elif profile==2:#including incidence angle effect
                    z0=(((zz[7]**expo)/(ur**expo))*(((ac**2)*np.absolute(math.cos(inci))/zz[2])+alpha_wc))+(0.11*zz[6]/zz[7])
                    K=(((zz[9]-(0.11*zz[6]/zz[7]))/(((zz[7]**2)/((ur**2)))))-((ac**2)*np.absolute(math.cos(inci))/zz[2]))
                    coeff2.append(K)
                elif profile==3:#including effective height correction
                    z0=(((zz[7]**2)/(ur**2))*((((ac*np.exp(-zz[0]/zz[2]))**2)/zz[2])+alpha_wc))+(0.11*zz[6]/zz[7])
                elif profile==4:#including gustiness
                    z0=(((zz[7]**2)/((ur**2)*(zz[8]**2)))*(((ac**2)/zz[2])+alpha_wc))+(0.11*zz[6]/zz[7])
                elif profile==5:#including gustiness and incidence
                    z0=(((zz[7]**2)/((ur**2)*(zz[8]**2)))*(((ac**2)*np.absolute(math.cos(inci))/zz[2])+alpha_wc))+(0.11*zz[6]/zz[7])
                elif profile==6:#including all the above
                    z0=(((zz[7]**2)/((ur**2)*(zz[8]**2)))*((((ac*np.exp(-zz[0]/zz[2]))**2)*np.absolute(math.cos(inci))/zz[2])+alpha_wc))+(0.11*zz[6]/zz[7])
                    Q=(((zz[9]-(0.11*zz[6]/zz[7]))/(((zz[7]**2)/((ur**2)*(zz[8]**2)))))-(((ac*np.exp(-zz[0]/zz[2]))**2)*np.absolute(math.cos(inci))/zz[2]))
                    coeff.append(Q)
                elif profile==7:#rabaneda's method
                    z0=(((zz[7]/ur)**(1/0.41))*(np.average(self.joint2['WAVELENGHT(m)']))*(1+(zz[0]/(zz[0]-ac))))+(0.11*zz[6]/zz[7])
                roughis.append(z0)
        self.df['z01']=roughis
        if len(coeff)!=0:
            self.df['Coefficient']=coeff
        else:
            pass
        if len(coeff2)!=0:
            self.df['Coefficient_no_gust']=coeff2
        else:
            pass
        if len(coeff2)!=0:
            self.df['ac']=aces
        else:
            pass
        
    def z0_wave_profile_iter(self, name, profile=1):
        '''Calculates the highest point of the wave crest in relation with SWL'''
        #wind-wave method
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Starting iterations >>>'
        zipi=zip(self.joint2['SIGNIFICANT_WAVE(m)'], self.joint2['WAVEPERIOD(s)'], self.joint2['WAVELENGHT(m)'],self.df['Wspd1'], self.df['Wdir'], self.joint2['Wave_direction'], self.df['kinematic'], self.df['u*1'], self.joint2['Gustiness'])
        #(H, T, L, wsp, wd, wave_dir, v, fric, G)
        roughis=[]
        betas=[]
        spidi=[]
        q=0
        for zz in zipi:
            foo=zz[0]/(9.81*zz[1]**2)
            k=2*np.pi/zz[2]
            E=k*zz[0]/2
            if zz[0]/zz[2]>(1/7.):
                roughis.append(np.nan)
            else:
                if foo<=0.001:
                    ac=zz[0]/2.
                elif foo>0.001 and foo<0.0075:
                    ac=(zz[0]/2.)+(0.5*E**2)
                elif foo>=0.0075:
                    ac=(zz[0]/2.)+(0.5*E**2)+((2/3.)*E**4)
                inci=np.absolute(math.radians(zz[4])- math.radians(zz[5]))                    
                if profile==1:
                    B=zz[2]*(1+(zz[0]/(zz[0]-ac)))
                elif profile==2:
                    B=(((ac**2)/(zz[2]))*np.absolute(math.cos(inci)))
                elif profile==3:
                    B=(((ac*np.exp(-zz[0]/zz[2]))**2)/(zz[2]))
                elif profile==4:
                    B=((((ac*np.exp(-zz[0]/zz[2]))**2)/(zz[2]))*np.absolute(math.cos(inci)))
                elif profile==5:
                    B=(((ac**2)/(zz[2]*zz[8]))*np.absolute(math.cos(inci)))
                betas.append(B)
                for i in np.arange(0.0000001, 2.5, 0.00000001):#iterating over z0
                    sea=(((0.41/np.log(10/i))**(1/0.41))*B)+(0.11*zz[6]/zz[7])
                    insitu=str("%.8f"%i)
                    friki=str("%.8f"%sea)
                    if friki==insitu:
                        roughis.append(sea)
                        spidi.append(i)
                        q+=1
                        print q
                        break
                    else:
                        if i>2.49:
                            print 'z0 not found'
                            roughis.append(np.nan)
                            spidi.append(np.nan)
                            break
                        else:
                            continue
                        
        self.df['z01']=roughis
        self.df[name]=betas
            
    def roughness_log_law(self):
        '''To calculate re lative speed I need current measurements, phase speed is not valid. Until then, relative speed can be considered wind speed since U0 use to be very small in comparison with wind speed'''        
        '''By the moment I'm not using gustiness'''
        
        speed=self.one
        #direc='Wdir'
        #self.df['Rel_speed(m/s)']=(((self.df[speed]*np.sin(self.df[direc]*(2*np.pi/360))-(self.joint2['Phase_speed']*np.sin(self.joint2['Wave_direction']*(2*np.pi/360))))**2)+((self.df[speed]*np.cos(self.df[direc]*(2*np.pi/360))-(self.joint2['Phase_speed']*np.cos(self.joint2['Wave_direction']*(2*np.pi/360))))**2))**(1./2)
        #drag=[(self.df['u*1']**2)/(self.joint2['Gustiness']*self.df['Rel_speed(m/s)']**2)]
        self.df['Rel_speed(m/s)']=list(self.df[speed])
        #self.df['z01']=10/(np.e**(0.4/(((self.df['u*1']**2)/(self.joint2['Gustiness']*(self.df['Rel_speed(m/s)']**2)))**(1./2))))
        self.df['z01']=10/(np.e**(0.4/(((self.df['u*1']**2)/(1*(self.df['Rel_speed(m/s)']**2)))**(1./2))))
        
    def k_viscosity(self):
        
        if self.term=='long':
            
            joint3=self.joint2.set_index('Device', drop=True)
            devices=self.df['Device'].unique()
            for dev in devices:
                P=np.average(joint3['PRESSURE(hPa)'].ix[dev])
                T=np.average(joint3['TEMPERATURE(C)'].ix[dev])
                H=np.average(joint3['HUMIDITY(%)'].ix[dev])
                dry_density=(P*100)/(287.05*(T+273.15)) #result in kg/m3
                density=(dry_density*(1+H/100))/(1+((H/100)*461.5/287.05))
                viscosity=((1.458*10**-6)*((T+273.15)**(3./2)))/(T+ 273.15 + 110.4)
                self.df['kinematic']=viscosity/density
                
        elif self.term=='instant':
            
            self.joint2['dry_density']=(self.joint2['PRESSURE(hPa)']*100)/(287.05*(self.joint2['TEMPERATURE(C)']+273.15)) #result in kg/m3
            self.joint2['density']=(self.joint2['dry_density']*(1+self.joint2['HUMIDITY(%)']/100))/(1+((self.joint2['HUMIDITY(%)']/100)*461.5/287.05))
            self.joint2['viscosity']=((1.458*10**-6)*((self.joint2['TEMPERATURE(C)']+273.15)**(3./2)))/(self.joint2['TEMPERATURE(C)']+ 273.15 + 110.4)
            self.joint2['kinematic']=self.joint2['viscosity']/self.joint2['density']
            self.df['kinematic']=list(self.joint2['kinematic'])
        
        try:
            del joint3
        except UnboundLocalError:
            pass
        
    
    def min_z0(self, kinematic, charnock=None, w_height=None, w_length=None, mode='fetch', mode2=True):
        '''To calculate min roughness, which represents the minimum intersections between smooth-trans(zst) or smooth-rough(zsr) or smooth-wave(zsw)'''
        '''The method substitute calculate roughness on dataframe self.df'''
        '''kinematic, charnock, w_height and w_length are arrays. mode is to choose between wave and fetch. If mode=wave it is only compared
        smooth-trans and smooth-wave. If mode=fetch it is only compared smooth-trans and smooth-rough.'''

        if mode2==False or self.how=='sea_shape':
            pass
        else:
            if self.term=='long':
                
                if mode=='fetch':
                    zst=0.004428*(np.average(kinematic)**(2./3))
                    zsr=0.4915*((np.average(kinematic)**2)*np.average(charnock))**(1./3)
                    z_min=np.min([zst, zsr])
    
                elif mode=='wave':
                   zst=0.004428*(np.average(kinematic)**(2./3))
                   zsw=0.0887*((np.average(kinematic)**2)*(np.average(w_height)/np.average(w_length)))**(1./3)
                   z_min=np.min([zst, zsw])
            
            elif self.term=='instant':
                
                z_min=[]
                if mode=='fetch':
                    for x in zip(kinematic, charnock):
                        zst=0.004428*(x[0]**(2./3))
                        zsr=0.4915*((x[0]**2)*x[1])**(1./3)
                        z_mini=np.min([zst, zsr])
                        z_min.append(z_mini)
                elif mode=='wave':
                   for x in zip(kinematic, w_height, w_length):
                       zst=0.004428*(x[0]**(2./3))
                       zsw=0.0887*((x[0]**2)*(x[1]/x[2]))**(1./3)
                       z_mini=np.min([zst, zsw])
                       z_min.append(z_mini)
                       
            self.df['z_min']=z_min #This is not necessary is just to check if it's working properly
            z01=[]
            for z in zip(list(self.df['z01']), z_min):
                if z[0]<z[1]:
                    z01.append(z[1])
                else:
                    z01.append(z[0])
            self.df['z01']=z01
            
            if 'Wspd2' in self.df.columns:
                z02=[]
                for z in zip(list(self.df['z02']), z_min):
                    if z[0]<z[1]:
                        z02.append(z[1])
                    else:
                        z02.append(z[0])
                self.df['z02']=z02
            else:
                pass
            if 'Wspd3' in self.df.columns:
                z03=[]
                for z in zip(list(self.df['z03']), z_min):
                    if z[0]<z[1]:
                        z03.append(z[1])
                    else:
                        z03.append(z[0])
                self.df['z03']=z03
            else:
                pass
    

    def z_regim(self, kinematic, w_height, w_length, friction, smooth, trans, rough):
        '''To know under what roughness regim the measurements were taken. This is only used for wave methodology'''
        '''kinematic, w_height, w_length and friction are array_like'''

        if self.term=='long':
            x=zip(np.average(kinematic), np.average(w_height), np.average(w_length), np.average(friction), np.average(smooth), np.average(trans), np.average(rough))
            ust=2.484*(x[0]**(1./3))
            usw=1.24*(x[0]*x[2]/x[1])**(1./3)
            if ust<usw:
                utw=0.28746*((x[0]*x[2]**2)/x[1]**2)**(1./3)
                if x[3]<ust:
                    yield x[4] #smooth regim
                elif x[3]>ust and x[3]<utw:
                    yield x[5] #trans regim
                elif x[3]>ust and x[3]>utw:
                    yield x[6] #wave regim
            elif ust>usw: #no trans regim
                if x[3]<usw:
                    yield x[4] #smooth regim
                elif x[3]>usw:
                    yield x[6] #wave regim
        elif self.term=='instant':
           for x in zip(kinematic, w_height, w_length, friction, smooth, trans, rough):
               ust=2.484*(x[0]**(1./3))
               usw=1.24*(x[0]*x[2]/x[1])**(1./3)
               if ust<usw:
                   utw=0.28746*((x[0]*x[2]**2)/x[1]**2)**(1./3)
                   if x[3]<ust:
                       yield x[4] #smooth regim
                   elif x[3]>ust and x[3]<utw:
                       yield x[5] #trans regim
                   elif x[3]>ust and x[3]>utw:
                       yield x[6] #wave regim
               elif ust>usw: #no trans regim
                   if x[3]<usw:
                       yield x[4] #smooth regim
                   elif x[3]>usw:
                       yield x[6] #wave regim
                       
    def z_regim2(self, kinematic, charnock, friction, smooth, trans, rough):
        '''To know under what roughness regim the measurements were taken. This is used for methodologies that calculates Charnock parameter'''
        '''kinematic, charnock and friction are array_like'''

        if self.term=='long':
            x=zip(np.average(kinematic), np.average(charnock), np.average(friction), np.average(smooth), np.average(trans), np.average(rough))
            ust=2.484*(x[0]**(1./3))
            usr=1.0257*(x[0]/x[1])**(1./3)
            if ust<usr:
                utr=0.4235*(x[0]/x[1]**2)**(1./3)
                if x[2]<ust:
                    yield x[3] #smooth regim
                elif x[2]>ust and x[2]<utr:
                    yield x[4] #trans regim
                elif x[2]>ust and x[2]>utr:
                    yield x[5] #rough regim
            elif ust>usr: #no trans regim
                if x[2]<usr:
                    yield x[3] #smooth regim
                elif x[2]>usr:
                    yield x[5] #rough regim
        elif self.term=='instant':
           for x in zip(kinematic, charnock, friction, smooth, trans, rough):
               ust=2.484*(x[0]**(1./3))
               usr=1.0257*(x[0]/x[1])**(1./3)
               if ust<usr:
                   utr=0.4235*(x[0]/x[1]**2)**(1./3)
                   if x[2]<ust:
                       yield x[3] #smooth regim
                   elif x[2]>ust and x[2]<utr:
                       yield x[4] #trans regim
                   elif x[2]>ust and x[2]>utr:
                       yield x[5] #rough regim
               elif ust>usr: #no trans regim
                   if x[2]<usr:
                       yield x[3] #smooth regim
                   elif x[2]>usr:
                       yield x[5] #rough regim
    
    def air_sea(self, mode=None, mode2=True, itera=False):
        '''Calculating surface roughness according to atmospheric and wave parameters'''
        
        if self.term=='long':
            
            joint3=self.joint2.set_index('Device', drop=True)
            devices=self.df['Device'].unique()
            one={}
            two={}
            three={}
            for dev in devices:
                
                if itera==False:
                    Hs=np.average(joint3['SIGNIFICANT_WAVE(m)'].ix[dev])
                    W=np.average(joint3['WAVELENGHT(m)'].ix[dev])
                    smooth=0.11*self.df['kinematic'].ix[dev].unique()/np.average(joint3['u*1'].ix[dev])
                    trans=0.1*((self.df['kinematic'].ix[dev].unique()*np.average(joint3['u*1'].ix[dev])/9.81)**0.5)
                    rough=self.rough_sea(dev, Hs=Hs, W=W, joint3=joint3, mode=mode)
                    g=self.z_regim(self.df['kinematic'].ix[dev].unique(), Hs, W, joint3['u*1'].ix[dev].astype(float), smooth, trans, rough)
                    z=g.next()
                    one[dev]=z
                    if 'Wspd2' in self.df.columns:            
                        smooth=0.11*self.df['kinematic'].ix[dev].unique()/np.average(joint3['u*2'])
                        trans=0.1*((self.df['kinematic'].ix[dev].unique()*np.average(joint3['u*2'])/9.81)**0.5)
                        rough=0.09*Hs*(2*np.pi/W)*(np.average(joint3['u*2'])**2)/9.81
                        g=self.z_regim(self.df['kinematic'].ix[dev].unique(), Hs, W, joint3['u*2'].ix[dev].astype(float), smooth, trans, rough)
                        z=g.next()
                        two[dev]=z
                    else:
                        two[dev]=np.nan
                    if 'Wspd3' in self.df.columns:
                        smooth=0.11*self.df['kinematic'].ix[dev].unique()/np.average(joint3['u*3'])
                        trans=0.1*((self.df['kinematic'].ix[dev].unique()*np.average(joint3['u*3'])/9.81)**0.5)
                        rough=0.09*Hs*(2*np.pi/W)*(np.average(joint3['u*3'])**2)/9.81
                        g=self.z_regim(self.df['kinematic'].ix[dev].unique(), Hs, W, joint3['u*3'].ix[dev].astype(float), smooth, trans, rough)
                        z=g.next()
                        three[dev]=z
                    else:
                        three[dev]=np.nan
            self.df.set_index('Device', inplace=True)
            self.df['z01']=pd.Series(one)
            self.df['z02']=pd.Series(two)
            self.df['z03']=pd.Series(three)
            self.df.reset_index(inplace=True)
            self.min_z0(list(self.df['kinematic']), w_height=list(joint3['SIGNIFICANT_WAVE(m)']), w_length=list(joint3['WAVELENGHT(m)']), mode='wave', mode2=mode2)
            del joint3

        elif self.term=='instant':
            
            self.rough_sea(mode=mode)
            if itera==False:
                self.joint2['smooth']=0.11*(self.joint2['kinematic']/self.df['u*1'])
                self.joint2['trans']=0.1*((self.joint2['kinematic']*self.df['u*1']/9.81)**0.5)
                g=self.z_regim(list(self.joint2['kinematic'].astype(float)), list(self.joint2['SIGNIFICANT_WAVE(m)'].astype(float)), list(self.joint2['WAVELENGHT(m)'].astype(float)), list(self.df['u*1'].astype(float)), list(self.joint2['smooth'].astype(float)), list(self.joint2['trans'].astype(float)), list(self.joint2['rough'].astype(float)))
                self.df['z01']=list(g)
            else:
                self.df['z01']=self.joint2['rough']
                
            if 'Wspd2' in self.df.columns:
                if itera==False:
                    self.joint2['smooth2']=0.11*(self.joint2['kinematic']/self.df['u*2'])
                    self.joint2['trans2']=0.1*((self.joint2['kinematic']*self.df['u*2']/9.81)**0.5)
                    self.joint2['rough2']=0.09*self.joint2['SIGNIFICANT_WAVE(m)']*(2*np.pi/self.joint2['WAVELENGHT(m)'])*(self.df['u*2']**2)/9.81
                    g=self.z_regim(list(self.joint2['kinematic'].astype(float)), list(self.joint2['SIGNIFICANT_WAVE(m)'].astype(float)), list(self.joint2['WAVELENGHT(m)'].astype(float)), list(self.df['u*2'].astype(float)), list(self.joint2['smooth'].astype(float)), list(self.joint2['trans'].astype(float)), list(self.joint2['rough'].astype(float)))
                    self.df['z02']=list(g)
                else:
                    self.rough_sea(mode=mode)
                    self.df['z02']=self.joint2['rough']
            else:
                self.df['z02']=np.nan
            if 'Wspd3' in self.df.columns:
                if itera==False:
                    self.joint2['smooth3']=0.11*(self.joint2['kinematic']/self.df['u*3'])
                    self.joint2['trans3']=0.1*((self.joint2['kinematic']*self.df['u*3']/9.81)**0.5)
                    self.joint2['rough3']=0.09*self.joint2['SIGNIFICANT_WAVE(m)']*(2*np.pi/self.joint2['WAVELENGHT(m)'])*(self.df['u*3']**2)/9.81
                    g=self.z_regim(list(self.joint2['kinematic'].astype(float)), list(self.joint2['SIGNIFICANT_WAVE(m)'].astype(float)), list(self.joint2['WAVELENGHT(m)'].astype(float)), list(self.df['u*3'].astype(float)), list(self.joint2['smooth'].astype(float)), list(self.joint2['trans'].astype(float)), list(self.joint2['rough'].astype(float)))
                    self.df['z03']=list(g)
                else:
                    self.rough_sea(mode=mode)
                    self.df['z03']=self.joint2['rough']
            else:
                self.df['z03']=np.nan
            if itera==False:
                self.min_z0(list(self.df['kinematic']), w_height=list(self.joint2['SIGNIFICANT_WAVE(m)']), w_length=list(self.joint2['WAVELENGHT(m)']), mode='wave', mode2=mode2)
   
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Roughness calculated >>>'

    def rough_sea(self,dev=None, Hs=None, W=None, joint3=None, mode=None):
        '''only to calculate rough surface roughness for sea_state or wave methods'''
        
        if self.how=='wave' or mode=='wave':
            if self.term=='long':
                rough=0.09*Hs*(2*np.pi/W)*(np.average(joint3['u*1'].ix[dev])**2)/9.81
                return rough
            elif self.term=='instant':
                self.joint2['rough']=0.09*self.joint2['SIGNIFICANT_WAVE(m)']*(2*np.pi/self.joint2['WAVELENGHT(m)'])*(self.df['u*1']**2)/9.81
        elif self.how=='sea_shape' or mode=='sea_shape':
            if self.term=='long':
                rough=(1200*(Hs/W)**4.5)*Hs
                return rough
            elif self.term=='instant':
                self.joint2['rough']=(1200*(self.joint2['SIGNIFICANT_WAVE(m)']/self.joint2['WAVELENGHT(m)'])**4.5)*self.joint2['SIGNIFICANT_WAVE(m)']


       
    def frame_ref(self, cha=0.0144, save=False):
        '''Perpare a dataframe linking wind speed with friction velocity and surface roughness, wind speed as index'''
        '''According to Badge's methodology, through iteration'''
        
        indx=set()
        foo=DataFrame(columns=['u*','z0'])
        for i in np.arange(0.000001, 6, 0.000000001, dtype=np.float32):#using a precision of 0.0001 in friction velocity we have a precision of 0.01 in wind speed
            z0=((i**2)*cha)/9.81#Charnock parameter is constant here, 0.0144
            u=(np.log(10/z0))*(i/0.4)
            uz=str("%.2f"%u)
            if not uz in indx:
                indx.add(uz)
                foo.loc[uz]=[i, z0]
            else:
                continue
        foo.index.name='uz'
        foo=foo.reset_index()
        foo=foo.convert_objects(convert_numeric=True)
        self.reference=foo.set_index('uz')
        self.reference.to_csv('Refer.csv')
     
    def iterated(self):
        '''insert new columns into dataframe: friction velocity, surface roughness & lifted winds'''
        '''THERE WAS A PROBLEMMM HERE WHEN I was INDEXING WITH A FLOAT NUMBER, do the same than fino1.py to solve this, indexing with 2 decimals string number'''
        
        if self.term=='long':
            
            devices=self.df['Device'].unique()
            frame=self.df.set_index('Device', drop=True)
            one={}
            two={}
            three={}
            uno={}
            dos={}
            tres={}
            for dev in devices:
                one[dev]=self.reference.ix[str('%.2f'%np.average(frame[self.one].ix[dev]))]['u*']
                if 'Wspd2' in self.df.columns:            
                    two[dev]=self.reference.ix[str('%.2f'%np.average(frame[self.two].ix[dev]))]['u*']
                else:
                    two[dev]=np.nan
                if 'Wspd3' in self.df.columns:
                    three[dev]=self.reference.ix[str('%.2f'%np.average(frame[self.three].ix[dev]))]['u*']
                else:
                    three[dev]=np.nan
                    
                uno[dev]=self.reference.ix[str('%.2f'%np.average(frame[self.one].ix[dev]))]['z0'] 
                if 'Wspd2' in self.df.columns:           
                    dos[dev]=self.reference.ix[str('%.2f'%np.average(frame[self.two].ix[dev]))]['z0']
                else:
                    dos[dev]=np.nan
                if 'Wspd3' in self.df.columns:
                    tres[dev]=self.reference.ix[str('%.2f'%np.average(frame[self.three].ix[dev]))]['z0']
                else:
                    tres[dev]=np.nan
            self.df.set_index('Device', inplace=True)
            self.df['u*1']=pd.Series(one)
            self.df['u*2']=pd.Series(two)
            self.df['u*3']=pd.Series(three)
            self.df['z01']=pd.Series(uno)
            self.df['z02']=pd.Series(dos)
            self.df['z03']=pd.Series(tres)
            self.df.reset_index(inplace=True)

        elif self.term=='instant':
        
            self.df['u*1']=[self.reference.ix[str('%.2f'%x)]['u*'] for x in self.df[self.one]]
            if 'Wspd2' in self.df.columns:            
                self.df['u*2']=[self.reference.ix[str('%.2f'%x)]['u*'] for x in self.df[self.two]]
            else:
                self.df['u*2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['u*3']=[self.reference.ix[str('%.2f'%x)]['u*'] for x in self.df[self.three]]
            else:
                self.df['u*3']=np.nan
                
            self.df['z01']=[self.reference.ix[str('%.2f'%x)]['z0'] for x in self.df[self.one]] 
            if 'Wspd2' in self.df.columns:            
                self.df['z02']=[self.reference.ix[str('%.2f'%x)]['z0'] for x in self.df[self.two]]
            else:
                self.df['z02']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['z03']=[self.reference.ix[str('%.2f'%x)]['z0'] for x in self.df[self.three]]
            else:
                self.df['z03']=np.nan
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Friction velocity and roughness calculated >>>'
            
    def z_cw(self, name):
        '''Calculates roughness produced by composition of waves'''
        
        self.df[name]=self.joint2['Roughness']-self.df['z01']

               
    def lifted(self, way):
        '''Extrapolating winds according the log law, using surface roughness and friction velocity as unique parameters. Stability correction is NOT included'''

        if self.term=='long':
            
            devices=self.df['Device'].unique()
            frame=self.df.set_index('Device', drop=True)
            one={}
            two={}
            three={}
            for dev in devices:
                one[dev]=(np.log(self.height/np.average(frame['z01'].ix[dev])))*(np.average(frame['u*1'].ix[dev]/0.4))
                if 'Wspd2' in self.df.columns:            
                    two[dev]=(np.log(self.height/np.average(frame['z02'].ix[dev])))*(np.average(frame['u*2'].ix[dev]/0.4))
                else:
                    two[dev]=np.nan
                if 'Wspd3' in self.df.columns:
                    three[dev]=(np.log(self.height/np.average(frame['z03'].ix[dev])))*(np.average(frame['u*3'].ix[dev]/0.4))
                else:
                    three[dev]=np.nan
            self.df.set_index('Device', inplace=True)
            self.df['Wlifted1']=pd.Series(one)
            self.df['Wlifted2']=pd.Series(two)
            self.df['Wlifted3']=pd.Series(three)
            self.df.reset_index(inplace=True)
                
        elif self.term=='instant':
            
            self.df['Wlifted1']=(np.log(self.height/self.df['z01']))*(self.df['u*1']/0.4)
            if 'Wspd2' in self.df.columns:           
                self.df['Wlifted2']=(np.log(self.height/self.df['z02']))*(self.df['u*2']/0.4)
            else:
                self.df['Wlifted2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['Wlifted3']=(np.log(self.height/self.df['z03']))*(self.df['u*3']/0.4)
            else:
                self.df['Wlifted3']=np.nan  
                
        self.df[way]=self.df['Wlifted1']
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Winds already extrapolated >>>'
    

    def drag(self):

        if self.term=='long':
            
            devices=self.df['Device'].unique()
            frame=self.df.set_index('Device', drop=True)
            one={}
            two={}
            three={}
            for dev in devices:
                one[dev]=((0.4/(np.log(10/frame['z01'].unique())))**2)*1000
                if 'Wspd2' in self.df.columns:            
                    two[dev]=((0.4/(np.log(10/frame['z02'].unique())))**2)*1000
                else:
                    two[dev]=np.nan
                if 'Wspd3' in self.df.columns:
                    three[dev]=((0.4/(np.log(10/frame['z03'].unique())))**2)*1000
                else:
                    three[dev]=np.nan
                    
            self.df.set_index('Device', inplace=True)
            self.df['Cd1']=pd.Series(one)
            self.df['Cd2']=pd.Series(two)
            self.df['Cd3']=pd.Series(three)
            
        elif self.term=='instant':
            self.df['Cd1']=((0.4/(np.log(10/self.df['z01'])))**2)*1000 
            if 'Wspd2' in self.df.columns:           
                self.df['Cd2']=((0.4/(np.log(10/self.df['z02'])))**2)*1000
            else:
                self.df['Cd2']=np.nan
            if 'Wspd3' in self.df.columns:
                self.df['Cd3']=((0.4/(np.log(10/self.df['z03'])))**2)*1000
            else:
                self.df['Cd3']=np.nan  
            

class Prepare_sat:
    '''Produce columns cell_center, device, date and day/night necesary to index'''
    
    data=object()
    
    def __init__(self, dataframe):
        
        self.df=dataframe
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Preparing dataframe >>>'
        
    def reindexing(self):
        
        indexes1=list(self.df.index.names)
        fofo=self.df.reset_index()
        foo=self.set_clock(fofo)
        if 'Satellite' in indexes1:            
            bas=foo.rename(columns={'Satellite':'Device'})
            self.data=bas
        elif 'Instrument' in indexes1:
            bas=foo.rename(columns={'Instrument':'Device'})
            self.data=bas
        else:
            foo['Device']='Satellites'
            self.data=foo
                    
    def set_clock(self, dataframe):
        '''Creates a new column to set when it's day or night, it's not considered seasonal variations'''
        
        #maxim=max(list(dataframe.index))+1
        #monthlist=[]
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
        dataframe['Day/Night']=days
        print str(a)+' time errors'
        return dataframe
        
    def execution(self):
        
        self.reindexing()
        return self.data
            
            
class Sat_calcs:
    '''dataframe named calc_df is the dataframe with results to plot'''    
    
    def __init__(self, basis, months, year, dataframe, height, term='long', period=None):
        
        self.calc_df=object()
        self.dates=[]
        self.basis=basis
        self.data=dataframe
        self.year=year
        self.months=months
        self.period=period
        self.height=height
        self.term=term
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Calculating statistics >>>' 
            
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
            days=data.index.get_level_values(levels[3]).unique()
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
            level4=list(days)            
            indexes=pd.MultiIndex.from_arrays([level1, level2*A, level3*(A*B), level4*(A*B*C)], names=levels)
            
        cols=[['Temperature', 'Temperature', 'Temperature', 'Temperature', 'Pressure', 'Pressure', 'Pressure', 'Pressure', 'Humidity', 'Humidity', 'Humidity', 'Humidity', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed1', 'Wspeed2', 'Wspeed3', 'Wspeed4', 'Wspeed5'], ['Average', 'Min', 'Max', 'Sdeviation', 'Average', 'Min', 'Max', 'Sdeviation', 'Average', 'Min', 'Max', 'Sdeviation', 'Average', 'Min', 'Max', 'Sdeviation', 'Roughness', 'Hubspeed', 'C', 'K', 'AED', 'WPD', 'Effective_ws', 'WPD_100', 'WPD_200', 'Samples', 'Average', 'Average', 'Average', 'Average']]
        self.calc_df=DataFrame(index=indexes, columns=cols)
        
    def set_dates(self):
        
        mesos={'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6, 'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
        meses=list(self.months)
        yes=list(self.year)
        years=set()            
        if yes[0]=='All':
            annos=self.data['Date'].unique()
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
                years.add(i)
                        
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
     
    def sat_by_period(self):
        '''Indexing by date and time, and then same as sat_all_years'''
        
        if self.period[0]!=None and self.period[2]!=None:
            DFrame=self.data.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            framing=DF[self.period[0]:self.period[1]]
            dframing=framing.set_index('Time', drop=False)
            frame=dframing.sort_index()
            table=frame[self.period[2]:self.period[3]]
        elif self.period[0]!=None and self.period[2]==None:
            DFrame=self.data.set_index('Date', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[0]:self.period[1]]
        elif self.period[0]==None and self.period[2]!=None:
            DFrame=self.data.set_index('Time', drop=False)
            DF=DFrame.sort_index()
            table=DF[self.period[2]:self.period[3]]
        self.data=table
        
    
    def sat_all_years(self):
        
        DF=self.data.set_index(['cell_center', 'Device'])
        self.new_frame(DF)
        cells=DF.index.get_level_values('cell_center').unique()
        devices=DF.index.get_level_values('Device').unique()
       
        for row in cells:
            for dev in devices:
                try:
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Average'), round(np.average(pd.Series(DF['Wspd1'].ix[row].ix[dev]).dropna()), 2))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Roughness'), np.average(pd.Series(DF['z01'].ix[row].ix[dev]).dropna()))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Hubspeed'), np.average(pd.Series(DF['Wlifted1'].ix[row].ix[dev]).dropna()))                    
                    if self.term=='long':
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wspd1'].ix[row].ix[dev]).dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wspd1'].ix[row].ix[dev]).dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wspd1'].ix[row].ix[dev]).dropna()))
                        K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev], self.calc_df['Wspeed1']['Average'].ix[row].ix[dev], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev])
                    elif self.term=='instant':
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wlifted1'].ix[row].ix[dev]).dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wlifted1'].ix[row].ix[dev]).dropna()))
                        self.calc_df.set_value((row, dev), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wlifted1'].ix[row].ix[dev]).dropna()))
                        K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev])
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'AED'), self.aed(C, K))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev], [0, 4, 25, 100]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev]), [0, 100, 5000]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev]), [0, 200, 5000]))
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'Samples'), len(pd.Series(DF['Wspd1'].ix[row].ix[dev])))                    
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'C'), C)
                    self.calc_df.set_value((row, dev), ('Wspeed1', 'K'), K)
                except (KeyError, IndexError):
                    continue
                
                try:
                    self.calc_df.set_value((row, dev), ('Wspeed2', 'Average'), np.average(DF['Wspd2'].ix[row].ix[dev].dropna()))
                except (KeyError, IndexError):
                    continue
                
                try:
                    self.calc_df.set_value((row, dev), ('Wspeed3', 'Average'), np.average(DF['Wspd3'].ix[row].ix[dev].dropna()))                   
                except (KeyError, IndexError):
                    continue
                
    def sat_by_dates(self):
        '''By dates means to select by years or months, dates are already set'''
        
        if self.months[0]!='None' and self.year[0]=='None':
            self.data['Month']=self.data['Date'].dt.month
            DF=self.data.set_index(['cell_center', 'Device', 'Month'])
        elif self.year[0]!='None':
            DF=self.data.set_index(['cell_center', 'Device', 'Date'])
        self.new_frame(DF)
        cells=DF.index.get_level_values('cell_center').unique()
        devices=DF.index.get_level_values('Device').unique()
        
        for row in cells:
            for dev in devices:
                for date in self.dates:
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Average'), round(np.average(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()),2))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Roughness'), np.average(pd.Series(DF['z01'].ix[row].ix[dev].ix[date]).dropna()))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Hubspeed'), np.average(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))
                        if self.term=='long':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Average'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        elif self.term=='instant':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'AED'), self.aed(C, K))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev].ix[date], [0, 4, 25, 100]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 100, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 200, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Samples'), len(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date])))                        
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'C'), C)
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'K'), K)
                    except (KeyError, IndexError):
                        continue
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed2', 'Average'), np.average(DF['Wspd2'].ix[row].ix[dev].ix[date].dropna()))                        
                    except (KeyError, IndexError):
                        continue
                    
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed3', 'Average'), np.average(DF['Wspd3'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        continue
    
    def sat_by_daynight(self):
        
        DF=self.data.set_index(['cell_center', 'Device', 'Day/Night'])
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
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Average'), round(np.average(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()),2))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Roughness'), np.average(pd.Series(DF['z01'].ix[row].ix[dev].ix[date]).dropna()))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Hubspeed'), np.average(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))                        
                        if self.term=='long':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date]).dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Average'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        elif self.term=='instant':
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))
                            self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date]).dropna()))
                            K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date])
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'AED'), self.aed(C, K))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev].ix[date], [0, 4, 25, 100]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 100, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date]), [0, 200, 5000]))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'Samples'), len(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date])))
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'C'), C)
                        self.calc_df.set_value((row, dev, date), ('Wspeed1', 'K'), K)
                    except (KeyError, IndexError):
                        continue
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed2', 'Average'), np.average(DF['Wspd2'].ix[row].ix[dev].ix[date].dropna()))
                    except (KeyError, IndexError):
                        continue
                    
                    try:
                        self.calc_df.set_value((row, dev, date), ('Wspeed3', 'Average'), np.average(DF['Wspd3'].ix[row].ix[dev].ix[date].dropna()))                       
                    except (KeyError, IndexError):
                        continue
        
    
    def sat_by_date_and_night(self):
        
        if self.months[0]!='None' and self.year[0]=='None':
            self.data['Month']=self.data['Date'].dt.month
            DF=self.data.set_index(['cell_center', 'Device', 'Month', 'Day/Night'])
        elif self.year[0]!='None':
            DF=self.data.set_index(['cell_center', 'Device', 'Date', 'Day/Night'])
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
                for date in self.dates:
                    for base in dia:
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Average'), round(np.average(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base]).dropna()),2))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Roughness'), np.average(pd.Series(DF['z01'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Hubspeed'), np.average(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                            if self.term=='long':
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                                K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date].ix[base], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base])
                            elif self.term=='instant':
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Min'), np.amin(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Max'), np.amax(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                                self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Sdeviation'), np.std(pd.Series(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]).dropna()))
                                K, C=self.sat_weibull(self.calc_df['Wspeed1']['Sdeviation'].ix[row].ix[dev].ix[date].ix[base], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base], self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base])
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'AED'), self.aed(C, K))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'WPD'), self.wpd(self.calc_df['Wspeed1']['Hubspeed'].ix[row].ix[dev].ix[date].ix[base]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Effective_ws'), self.ocurrence(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base], [0, 4, 25, 100]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'WPD_100'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]), [0, 100, 5000]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'WPD_200'), self.ocurrence(self.wpd(DF['Wlifted1'].ix[row].ix[dev].ix[date].ix[base]), [0, 200, 5000]))
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'Samples'), len(pd.Series(DF['Wspd1'].ix[row].ix[dev].ix[date].ix[base])))                     
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'C'), C)
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed1', 'K'), K)
                        except (KeyError, IndexError):
                            continue
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed2', 'Average'), np.average(DF['Wspd2'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            continue
                        
                        try:
                            self.calc_df.set_value((row, dev, date, base), ('Wspeed3', 'Average'), np.average(DF['Wspd3'].ix[row].ix[dev].ix[date].ix[base].dropna()))
                        except (KeyError, IndexError):
                            continue    
    
    
    def execution(self):
        
        if self.period!=None:
            self.sat_by_period()
        self.set_dates()
        if self.months[0]=='None' and self.basis=='None' and self.year[0]=='None':
            self.sat_all_years()
        elif self.months[0]!='None' or self.year[0]!='None' and self.basis=='None':
            self.sat_by_dates()
        elif self.months[0]=='None' and self.year[0]=='None' and self.basis!='None':
            self.sat_by_daynight()
        elif self.months[0]!='None' or self.year[0]!='None' and self.basis!='None':
            self.sat_by_date_and_night()
        else:
            sys.exit('No calculations')
        self.calc_df.sort_index(level='cell_center', inplace=True)
        #self.calc_df.fillna(np.nan, inplace=True)
        self.calc_df.dropna(how='all', inplace=True)
        print '\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Statistics already calculated >>>' 
        return self.calc_df
            
               

        
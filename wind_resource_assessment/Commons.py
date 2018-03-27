# -*- coding: utf-8 -*-
"""
Created on Sun May  8 18:07:57 2016

@author: Alberto S. Rabaneda
"""
from datetime import datetime
import math

def timestamp(frame):
    '''frame needs to have Date and Time columns and this method return frame with Timestamp'''
    
    #try:
     #   frame['Timestamp']=datetime(frame['Date'].year, frame['Date'].month, frame['Date'].day, frame['Time'].hour, frame['Time'].minute, frame['Time'].second)
    #except AttributeError:
     #   frame['Timestamp']=datetime(datetime(frame['Date']).year, datetime(frame['Date']).month, datetime(frame['Date']).day, datetime(frame['Time']).hour, datetime(frame['Time']).minute, datetime(frame['Time']).second)
    #THIS IS NOT WORKING
    
    try:
        years = [x.year for x in frame['Date']]
        months = [x.month for x in frame['Date']]
        days = [x.day for x in frame['Date']]
    except AttributeError:
        years = [datetime(x).year for x in frame['Date']]
        months = [datetime(x).month for x in frame['Date']]
        days = [datetime(x).day for x in frame['Date']]
    try:
        hours = [x.hour for x in frame['Time']]
        minutes = [x.minute for x in frame['Time']]
        seconds = [x.second for x in frame['Time']]
    except AttributeError:
        hours = [datetime(x).hour for x in frame['Time']]
        minutes = [datetime(x).minute for x in frame['Time']]
        seconds = [datetime(x).second for x in frame['Time']]
    stamps=[]    
    for i in range(len(frame['Date'])):
        row=datetime(years[i], months[i], days[i], hours[i], minutes[i], seconds[i])
        stamps.append(row)
    frame['Timestamp']=stamps
    return frame
    
def inver_dir(frame):
    
    newdir=[]
    for x in frame['Wdir'].astype(float):
        if x>180:
            direc=x-180
        else:
            direc=x+180
        newdir.append(direc)
    frame['Wdir']=newdir
    return frame

def avg_angles(*args):
    '''average of list of angles in degrees'''
    
    radians=[math.radians(x) for x in args]
    si=(sum([math.sin(x) for x in radians]))/len(args)
    co=(sum([math.cos(x) for x in radians]))/len(args)
    pri=math.degrees(math.atan2(si,co))
    if pri<0:
        ang=pri+360
    else:
        ang=pri
    return ang
               
        
        

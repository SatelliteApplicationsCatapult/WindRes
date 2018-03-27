# -*- coding: utf-8 -*-
"""
Created on Wed Nov 04 19:10:40 2015

@author: Alberto S. Rabaneda
"""

import MySQLdb
import os
import pandas as pd
import sys

class FromDB:
    
    def __init__(self, coordenates, filepath):
        
        self.coord=coordenates
        self.path=filepath
        self.extraction()
    
    def connect(self):
        
        db=MySQLdb.connect(host="localhost",user="root",passwd="LA_0selva",db="oceanwinds2")
        cursor=db.cursor()
        return (db, cursor)
        
    def disconnect(self):
        
        db, cursor=self.connect()
        db.commit()
        cursor.close()
        db.close()
        
    def get_table(self):
        
        letter={10:'c',18:'d',26:'e',34:'f',42:'g',50:'h',58:'j',66:'k',74:'l',82:'m',90:'n',98:'p',106:'q',114:'r',122:'s',130:'t',138:'u',146:'v',154:'w',162:'x'}
        coord=self.coord
        vertex1=(coord[0],coord[2])
        vertex2=(coord[0],coord[3])
        vertex3=(coord[1],coord[2])
        vertex4=(coord[1],coord[3])
        vertexs=[vertex1, vertex2, vertex3, vertex4]
        utmtables=set()
        for ver in vertexs:
            if ver[1]>162:
                utmlat='x'
            else:
                for num in letter:
                    if num<=(ver[1]) and num>((ver[1])-8):
                        utmlat=(letter[num])
            utmlon=(int(ver[0]//6)+1)
            table=''.join([str(utmlon), utmlat])
            utmtables.add(table)
        print utmtables
        return utmtables
        
    def get_filepath(self):
        
        filepath=''.join([self.path, '/', 'DBoutput.csv'])
        if os.path.exists(filepath):
            for i in range(1,51):
                fil=('DBoutput'+str(i)+'.csv')
                filepath=''.join([self.path, '/', fil])
                if os.path.exists(filepath):
                    continue
                else:
                    return filepath.replace('//', '////')
                    break
        else:
            return filepath.replace('//', '////')

    def get_joinedpath(self):
        
        filepath=os.path.join(self.path, 'Merged_output.csv')
        if os.path.exists(filepath):
            for i in range(1,51):
                fil=('Merge_output'+str(i)+'.csv')
                filepath=os.path.join(self.path, fil)
                if os.path.exists(filepath):
                    continue
                else:
                    return filepath
                    break
        else:
            return filepath
    
    def join_files(self, args):
        #list of filepaths to join
        
        headers=['Satellite', 'Instrument', 'Long1', 'Long2', 'Lat1', 'Lat2', 'Date', 'Time', 'Wspd1', 'Wspd2', 'Wspd3', 'Wdir', 'Rain']
        name=self.get_joinedpath()
        print name
        if len(args)==1:
            a=pd.read_csv(args[0], names=headers, low_memory=False,  chunksize=100000, iterator=True)
            merged=pd.concat(a)
            merged.to_csv(name)
        elif len(args)==2:
            a=pd.read_csv(args[0], names=headers, low_memory=False,  chunksize=100000, iterator=True)
            b=pd.read_csv(args[1], names=headers, low_memory=False,  chunksize=100000, iterator=True)
            merged=pd.concat([a,b])
            merged.to_csv(name)            
        elif len(args)==4:
            a=pd.read_csv(args[0], names=headers, low_memory=False,  chunksize=100000, iterator=True)
            b=pd.read_csv(args[1], names=headers, low_memory=False,  chunksize=100000, iterator=True)
            c=pd.read_csv(args[2], names=headers, low_memory=False,  chunksize=100000, iterator=True)
            d=pd.read_csv(args[3], names=headers, low_memory=False,  chunksize=100000, iterator=True)
            supermerged=pd.concat([a,b,c,d])
            supermerged.to_csv(name)

    def remove_csv(self, args):
        #list of filepaths joined
    
        for files in args:
            os.remove(files)
                
    def extraction(self):
        
        db, cursor=self.connect()
        tables=list(self.get_table())
        tables.sort()
        coord=self.coord
        if len(tables)==1:
            allfiles=[]
            print 'one table'
            filepath=self.get_filepath()
            allfiles.append(filepath)
            sq1="SELECT * FROM " + str(tables[0]) + " WHERE Long1<" + str(coord[1]) + " AND Long2>" + str(coord[0]) + " AND Lat1<" + str(coord[3]) + " AND Lat2>" + str(coord[2]) + " INTO OUTFILE '" + filepath + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
            cursor.execute(sq1)
            self.disconnect()
        elif len(tables)==2:
            print 'two tables'
            allfiles=[]
            if tables[0][0]==tables[1][0]:#same longitude different latitude               
                filepath1=self.get_filepath()
                allfiles.append(filepath1)
                sq1="SELECT * FROM " + str(tables[0]) + " WHERE Long1<" + str(coord[1]) + " AND Long2>" + str(coord[0]) + " AND Lat2>" + str(coord[2]) + " INTO OUTFILE '" + filepath1 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
                cursor.execute(sq1)
                filepath2=self.get_filepath()
                allfiles.append(filepath2)
                sq2="SELECT * FROM " + str(tables[1]) + " WHERE Long1<" + str(coord[1]) + " AND Long2>" + str(coord[0]) + " AND Lat1<" + str(coord[3]) + " INTO OUTFILE '" + filepath2 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
                cursor.execute(sq2)
            elif tables[0][1]==tables[1][1]:#same latitude different longitude
                filepath1=self.get_filepath()
                allfiles.append(filepath1)
                sq1="SELECT * FROM " + str(tables[0]) + " WHERE Long2>" + str(coord[0]) + " AND Lat1<" + str(coord[3]) + " AND Lat2>" + str(coord[2]) + " INTO OUTFILE '" + filepath1 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
                cursor.execute(sq1)
                filepath2=self.get_filepath()
                allfiles.append(filepath2)
                sq2="SELECT * FROM " + str(tables[1]) + " WHERE Long1<" + str(coord[1]) + " AND Lat1<" + str(coord[3]) + " AND Lat2>" + str(coord[2]) + " INTO OUTFILE '" + filepath2 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
                cursor.execute(sq2)         
        elif len(tables)==4:
            print 'four tables'
            allfiles=[]
            filepath1=self.get_filepath()
            allfiles.append(filepath1)
            sq1="SELECT * FROM " + str(tables[0]) + " WHERE Long2>" + str(coord[0]) + " AND Lat2>" + str(coord[2]) + " INTO OUTFILE '" + filepath1 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
            cursor.execute(sq1)
            filepath2=self.get_filepath()
            allfiles.append(filepath2)
            sq2="SELECT * FROM " + str(tables[1]) + " WHERE Long2>" + str(coord[0]) + " AND Lat1<" + str(coord[3]) + " INTO OUTFILE '" + filepath2 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
            cursor.execute(sq2)
            filepath3=self.get_filepath()
            allfiles.append(filepath3)
            sq3="SELECT * FROM " + str(tables[2]) + " WHERE Long1<" + str(coord[1]) +  " AND Lat2>" + str(coord[2]) + " INTO OUTFILE '" + filepath3 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
            cursor.execute(sq3)
            filepath4=self.get_filepath()
            allfiles.append(filepath4)
            sq4="SELECT * FROM " + str(tables[3]) + " WHERE Long1<" + str(coord[1]) +  " AND Lat1<" + str(coord[3]) + " INTO OUTFILE '" + filepath4 + "' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
            cursor.execute(sq4)
        else:
            sys.exit('Selected aerea too big')
        self.disconnect()
        self.join_files(allfiles)
        self.remove_csv(allfiles)

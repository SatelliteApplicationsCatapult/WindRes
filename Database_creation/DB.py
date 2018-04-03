# -*- coding: utf-8 -*-
"""
Created on Fri Mar 30 17:07:24 2018

@author: Alberto S. Rabaneda
"""

import os
import MySQLdb

class Database:
    '''Inserting data from csv files into DB'''
    
    def __init__(self, csvdir):
        
        self.csvdir = csvdir
        self.user = raw_input('Insert user name to connect with MySQL: ')
        self.password = raw_input('Insert password for user '+self.user+' :')
        self.dbname = raw_input('Insert database name (for new database): ')
        self.db = None
        self.cursor = None
        
    def connect(self, dbname=None):
        '''Connecting with MySQL'''
        
        self.db = MySQLdb.connect("localhost", self.user, self.password, dbname)
        self.cursor = self.db.cursor()
        
    def disconnect(self,):
        '''Close connection with MySQL'''
        
        self.cursor.close()
        self.db.close()
        
    def create_db(self):
        '''To create a new database with 1200 tables representing UTM squares, fields are also defined'''
        
        db, cursor = self.connect()
        sq1 = "CREATE DATABASE '" + self.dbname + "';"
        sq2 = "USE '" + self.dbname + "'"
        self.cursor.execute(sq1)
        self.cursor.execute(sq2)
        sq3 = """CREATE TABLE 1c (FIRST_NAME CHAR(20) NOT NULL, LAST_NAME CHAR(20), AGE INT))"""
        self.cursor.execute(sq3)
        rows = ('c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x')
        for i in range(1, 61):
            for r in rows:
                table = ''.join([str(i), r])
                if table == '1c':
                    pass
                else:
                    sq4 = "CREATE TABLE '" + table + "' LIKE 1c ;"
                    cursor.execute(sq4)
        self.db.commit()
        
    def insert_data(self):
        '''Insert data from csv file into DB'''
        
        print 'Inserting data'
        for item in os.listdir(self.csvdir):
            print item
            filepath = ''.join([self.csvdir, '/', item])
            tablename = item.replace('.csv', '')
            sq1="LOAD DATA LOCAL INFILE '" + filepath + "' INTO TABLE " + tablename + " FIELDS TERMINATED BY ',' (Satellite, Instrument, Long1, Long2, Lat1, Lat2, Date, Time, Wspd1, Wspd2, Wspd3, Wdir) ;"
            self.cursor.execute(sq1)
            self.db.commit()
        self.disconnect()
        
    def indexes(self, Add=True):
        '''To add or remove indexes into/from tables of the DB'''
        #Indexes increase performance of MySQl DB

        print 'Adding/removing indexes'''
        letter=['c','d','e','f','g','h','j','k','l','m','n','p','q','r','s','t','u','v','w','x']
        for i in range(1,61):
            for var in letter:
                table=''.join([str(i),var])
                print table
                if Add == True:
                    sq1="ALTER TABLE "+table+" ADD INDEX "+'Myindex'+" (Long1, Long2, Lat1, Lat2);"
                elif Add == False:
                    sq1 = "ALTER TABLE "+table+" DROP INDEX "+'Myindex'+" (Long1, Long2, Lat1, Lat2);"
                self.cursor.execute(sq1)

        self.db.commit()

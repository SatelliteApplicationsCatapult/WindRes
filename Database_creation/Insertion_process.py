# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 17:02:40 2018

@author: Alberto S. Rabaneda
"""
from DB import Database
from Commons_db import CSV_Insertion
import sys


class Insertion:
    
    csvdir = None
    dataset_dir = None
    
    def __init__(self):
        
        print '\n>>>>>>>>>>>>>>>>>>>>>>> Welcome to WindRES project <<<<<<<<<<<<<<<<<<<<<<<<<<'
        print '\nThis is the ruotine to create a database with wind measurements from satellites'
        
    def decision_tree(self):
        '''Function to choose the process to undertake''' 
        
        print '\nThere are different options: '
        print '\t1. Convert datasets from different datahubs into csv files'
        print '\t2. Insert data from csv files into database'
        print '\t3. The whole process'
        
        opt = input('Select one of the above options (by number): ')
        
        print 'IMPORTANT !!! It is recommended to handle the full mission from one satellite, but no more than one satellite at once' 
        
        if opt == 1:
            self.only_csv()
        elif opt == 2:
            self.into_db()
        elif opt == 3:
            self.only_csv()
            self.into_db()
        else:
            sys.exit('Wrong answer, start again')
        
    def only_csv(self):
        
        self.dataset_dir = raw_input('Insert path to one satellite dataset directory/folder: ')
        self.csvdir = raw_input('Insert path to folder where csv files will be / were kept: '  )
        
        Sats=['All', 'Windsat', 'Quikscat', 'ASCAT', 'OSCAT', 'Rapidscat', 'Sentinel1', 'SSMIf08', 'SSMIf10', 'SSMIf11', 'SSMIf13', 'TMI', 'AMSR2', 'AMSRE']
        print '\nPossible satellites : '+str(Sats)
        sat = raw_input('\nWhat satellite would you like to process:')
        
        hubs=['Remote Sensing Systems', 'NASA', 'Sentinel1_tbx']
        print '\nInstrument options: '+str(hubs)
        datahub=raw_input('\nWhat datahub the datasets comes from:')
        
        Instru=['Radiometer', 'Scatterometer', 'SAR', 'Altimeter']
        print '\nInstrument options: '+str(Instru)
        inst=raw_input('\nWhat kind of instrument would you like to include:')
        
        csv = CSV_Insertion(self.csvdir, self.dataset_dir, datahub, sat, inst)
        if datahub == 'Remote Sensing Systems':
            csv.get_files_rss()
        elif datahub == 'NASA':
            csv.get_files_nasa()
        elif datahub == 'Sentinel1_tbx':
            csv.get_files_s1tbx()
        else:
            sys.exit('Wrong answer, start again')
        
    def into_db(self):
        
        if self.csvdir == None:
            self.csvdir = raw_input('Insert path to folder where csv files will be / were kept: '  )
        else:
            pass
        
        print 'There are different options'
        print '\ta. Just create the database'
        print '\tb. Create database and insert data into database by 1st time'
        print '\tc. Insert data into database without indexes or empty database'
        print '\td. Insert data into database with existing indexes (NON empty database)'
        choice = raw_input('Choose one option: ')

        db = Database(self.csvdir)
        if choice =='a':
            db.connect()
            db.create_db()
            db.disconnect()
        elif choice == 'b':
            db.connect()
            db.create_db()
            db.insert_data()
            idx = raw_input('Do you want to add indexes?(y/n): ')
            if idx == 'y':
                db.indexes()
            else:
                pass
            db.disconnect()
        elif choice == 'c':
            name = raw_input('\nInsert database name: ')
            db.connect(name)
            db.insert_data()
            idx = raw_input('Do you want to add indexes?(y/n): ')
            if idx == 'y':
                db.indexes()
            else:
                pass
            db.disconnect()
        elif choice == 'd':
            name = raw_input('\nInsert database name: ')
            db.connect(name)
            db.indexes(Add=False)
            db.insert_data()
            idx = raw_input('Do you want to add indexes?(y/n): ')
            if idx == 'y':
                db.indexes()
            else:
                pass
            db.disconnect()
            
            
#----------------------------------------------------------------------------------------------------------------

if __name__=='__main__':
    
    ins = Insertion()
    ins.decision_tree()
            
        
    
        
        
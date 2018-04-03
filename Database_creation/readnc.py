#! /usr/bin/env python
# file: readnc.py
# $id: $

import gzip
import os
from netCDF4 import Dataset

class NASAdaily:
    
    def __init__(self, filename, root):
        self.filename = filename
        self.root = root


    def read_nc(self):
        #to read a nc file
        ncfile=self.readgz()
        try:
            stream = Dataset( ncfile, 'r' )
        except IOError:
            print 'not a valid netCDF file'
        print self.filename, 'found'
        return stream
    
    def readGlobalAttrs(self, ds):
        # read and return global_atts
        attr_list = []
        global_attr = []
        #print 'Global attributes:'
        for attr_name in ds.ncattrs():
            #print attr_name, '=', getattr(nc_file, attr_name)
            attr_list.append( attr_name )
            atts = getattr( ds, attr_name )
            global_attr.append( atts )
        print 'Global attributes:'
        natts = len(attr_list)
        for n in range(0, natts):
            print attr_list[n]," = ",global_attr[n] 
    
    
    def readVars(self, ds):
        # read and return variables and their attributes
        #print 'Variables:' 
        #dictionary of variables:values
        var_attr_list = []
        var_data_list = []
        varis =  ds.variables.keys()
        for var_name in varis:
            attr = ds.variables[var_name]
            vardata = ds.variables[var_name][:]
            var_attr_list.append( attr )
            var_data_list.append( vardata)
        return varis, var_attr_list, var_data_list
    
    def readgz(self):
        #open nc.gz files and create nc file
        for subdir, dirs, files in os.walk(self.root):
            for item in files:
                if item==self.filename:
                    rightfile=os.path.join(subdir,item)
                    f = gzip.open(rightfile, 'rb')
                    stream = f.read()
                    nc_file=self.filename[:-3]
                    outF = open(nc_file, 'wb')
                    outF.write(stream)
                    f.close()
                    outF.close()
                    return nc_file
                    break
        
    def closing(self, ds):
        #for closing nc file and remove it
        ds.close()
        os.remove(self.readgz())

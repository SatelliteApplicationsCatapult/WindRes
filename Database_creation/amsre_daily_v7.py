#	This routine reads version-7 RSS AMSR-E daily files 
#
# 	filename  name of data file with path in form satname_yyyymmdd_v7.gz
#	 where satname  = name of satellite (amsre)
#	       yyyy		= year
#		   mm		= month
#		   dd		= day of month
#   missing = fill value used for missing data;
#                  if None, then fill with byte codes (251-255)

##	the output values correspond to:
#	time		time of measurement in fractional hours GMT
#	sst			sea surface temperature in deg Celsius
#	windLF		10m surface wind, low frequency, in meters/second
#	windMF		10m surface wind, medium frequency, in meters/second
#	vapor		columnar or integrated water vapor in millimeters
#	cloud		cloud liquid water in millimeters
#	rain		rain rate in millimeters/hour
#   longitude	Grid Cell Center Longitude', LON = 0.25*x_grid_location - 0.125 degrees east
#   latitude	Grid Cell Center Latitude',  LAT = 0.25*y_grid_location - 90.125
#   land		Is this land?
#   ice			Is this ice?
#   nodata		Is there no data
#
#   if you need help with this python read code, contact support@remss.com


from bytemaps import sys
from bytemaps import Dataset
from bytemaps import Verify


class AMSREdaily(Dataset):
    """ Read daily AMSRE bytemaps. """
    """
    Public data:
        filename = name of data file
        missing = fill value used for missing data;
                  if None, then fill with byte codes (251-255)
        dimensions = dictionary of dimensions for each coordinate
        variables = dictionary of data for each variable
    """

    def __init__(self, filename, root, missing=None):
        """
        Required arguments:
            filename = name of data file to be read (string)
                
        Optional arguments:
            missing = fill value for missing data,
                      default is the value used in verify file
        """
        self.filename = filename
        self.root = root
        self.missing = missing
        Dataset.__init__(self)

    # Dataset:

    def _attributes(self):
        return ['coordinates','long_name','units','valid_min','valid_max']

    def _coordinates(self):
        return ('orbit_segment','variable','latitude','longitude')

    def _shape(self):
        return (2,7,720,1440)

    def _variables(self):
        return ['time','sst','windLF','windMF','vapor','cloud','rain',
                'longitude','latitude','land','ice','nodata']

    # _default_get():

    def _get_index(self,var):
        return {'time' : 0,
                'sst' : 1,
                'windLF' : 2,
                'windMF' : 3,
                'vapor' : 4,
                'cloud':5,
                'rain':6,
                }[var]

    def _get_offset(self,var):
        return {'sst' : -3.0,
                'cloud' : -0.05,
                }[var]

    def _get_scale(self,var):
        return {'time' : 0.1,
                'sst' : 0.15,
                'windLF' : 0.2,
                'windMF' : 0.2,
                'vapor' : 0.3,
                'cloud' : 0.01,
                'rain' : 0.1,
                }[var]

    # _get_ attributes:

    def _get_long_name(self,var):
        return {'time' : 'Time of Day UTC',
                'sst' : 'Sea Surface Temperature',
                'windLF' : '10m Surface Wind Speed (low frequency)',
                'windMF' : '10m Surface Wind Speed (medium frequency)',
                'vapor' : 'Columnar Water Vapor',
                'cloud' : 'Cloud Liquid Water',
                'rain' : 'Surface Rain Rate',
                'longitude' : 'Grid Cell Center Longitude',
                'latitude' : 'Grid Cell Center Latitude',
                'land' : 'Is this land?',
                'ice' : 'Is this ice?',
                'nodata' : 'Is there no data?',
                }[var]

    def _get_units(self,var):
        return {'time' : 'fractional hours UTC',
                'sst' : 'deg Celsius',
                'windLF' : 'm/s',
                'windMF' : 'm/s',
                'vapor' : 'mm',
                'cloud' : 'mm',
                'rain' : 'mm/hr',
                'longitude' : 'degrees east',
                'latitude' : 'degrees north',
                'land' : 'True or False',
                'ice' : 'True or False',
                'nodata' : 'True or False',
                'land' : 'True or False',
                'ice' : 'True or False',
                'nodata' : 'True or False',
                }[var]

    def _get_valid_min(self,var):
        return {'time' : 0.0,
                'sst' : -3.0,
                'windLF' : 0.0,
                'windMF' : 0.0,
                'vapor' : 0.0,
                'cloud' : -0.05,
                'rain' : 0.0,
                'longitude' : 0.0,
                'latitude' : -90.0,
                'land' : False,
                'ice' : False,
                'nodata' : False,
                }[var]

    def _get_valid_max(self,var):
        return {'time' : 24.0,
                'sst' : 34.5,
                'windLF' : 50.0,
                'windMF' : 50.0,
                'vapor' : 75.0,
                'cloud' : 2.45,
                'rain' : 25.0,
                'longitude' : 360.0,
                'latitude' : 90.0,
                'land' : True,
                'ice' : True,
                'nodata' : True,
                }[var]              
    

class DailyVerify(Verify):
    """ Contains info for verification. """
    
    def __init__(self,dataset):
        self.filename = 'verify_amsre_v7.txt'
        self.ilon1 = 170
        self.ilon2 = 175
        self.ilat1 = 274
        self.ilat2 = 278                
        self.iasc = 1
        self.variables = ['time','sst','windLF','windMF','vapor','cloud','rain']
        self.startline = {'time' : 73,
                          'sst' : 80,
                          'windLF' : 87,
                          'windMF' : 94,
                          'vapor' : 101,
                          'cloud' : 108,
                          'rain' : 115 }
        Verify.__init__(self,dataset)
        

if __name__ == '__main__':
    """ Automated testing. """

    # read daily:
    amsr = AMSREdaily('AMSRE_20020715v7.gz')
    if not amsr.variables: sys.exit('file not found')
    
    # verify daily:
    verify = DailyVerify(amsr)    
    if verify.success: print('successful verification for daily')
    else: sys.exit('verification failed for daily')
    print('')

    print('all tests completed successfully')
    print('')

from bytemaps import sys
from bytemaps import Dataset
from bytemaps import Verify


class SSMIdaily(Dataset):
    """ Read daily SSMI bytemaps. """
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
        self.root= root
        self.missing = missing
        Dataset.__init__(self)

    # Dataset:

    def _attributes(self):
        return ['coordinates','long_name','units','valid_min','valid_max']

    def _shape(self):
        return (2,5,720,1440)

    def _coordinates(self):
        return ('orbit_segment','variable','latitude','longitude')
    
    def _variables(self):
        return ['time','wind','vapor','cloud','rain',
                'longitude','latitude','land','ice','nodata']                

    # _default_get():
    
    def _get_index(self,var):
        return {'time' : 0,
                'wind' : 1,
                'vapor' : 2,
                'cloud' : 3,
                'rain' : 4,
                }[var]

    def _get_scale(self,var):
        return {'time' : 0.1,
                'wind' : 0.2,
                'vapor' : 0.3,
                'cloud' : 0.01,
                'rain' : 0.1,
                }[var]

    def _get_offset(self,var):
        return {'cloud' : -0.05,
                }[var]

    # _get_ attributes:

    def _get_long_name(self,var):
        return {'time' : 'Fractional Hour GMT',
                'wind' : '10m Surface Wind Speed',
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
        return {'time' : 'Fractional Hour GMT',
                'wind' : 'm/s',
                'vapor' : 'mm',
                'cloud' : 'mm',
                'rain' : 'mm/hr',
                'longitude' : 'degrees east',
                'latitude' : 'degrees north',
                'land' : 'True or False',
                'ice' : 'True or False',
                'nodata' : 'True or False',
                }[var]

    def _get_valid_min(self,var):
        return {'time' : 0.0,
                'wind' : 0.0,
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
                'wind' : 50.0,
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
        self.filename = 'Verify_SSMI_v7.txt'
        self.ilon1 = 170
        self.ilon2 = 175
        self.ilat1 = 274
        self.ilat2 = 278                
        self.iasc = 1
        self.variables = ['time','wind','vapor','cloud','rain']
        self.startline = {'time' : 64,
                          'wind' : 71,
                          'vapor' : 78,
                          'cloud' : 85,
                          'rain' : 92 }
        Verify.__init__(self,dataset)
        

if __name__ == '__main__':
    """ Automated testing. """

    # read daily:
    ssmi = SSMIdaily('f10_19950120v7.gz')
    if not ssmi.variables: sys.exit('file not found')
    
    # verify daily:
    verify = DailyVerify(ssmi)
    if verify.success: print('successful verification for daily')
    else: sys.exit('verification failed for daily')
    print('')

    print('all tests completed successfully')
    print('')

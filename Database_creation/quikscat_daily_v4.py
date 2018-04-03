from bytemaps import sys
from bytemaps import Dataset
from bytemaps import Verify

from bytemaps import get_data
from bytemaps import ibits
from bytemaps import is_bad
from bytemaps import where


class QuikScatDaily(Dataset):
    """ Read daily QSCAT bytemaps. """
    """
    Public data:
        filename = name of data file
        missing = fill value used for missing data;
                  if None, then fill with byte codes (251-255)
        dimensions = dictionary of dimensions for each coordinate
        variables = dictionary of data for each variable
    """

    def __init__(self, filename, root, missing=-999.):
        """
        Required arguments:
            filename = name of data file to be read (string)
                
        Optional arguments:
            missing = fill value for missing data,
                      default is the value used in verify file
        """
        self.filename = filename
        self.root=root
        self.missing = missing
        Dataset.__init__(self)

    # Dataset:

    def _attributes(self):
        return ['coordinates','long_name','units','valid_min','valid_max']

    def _coordinates(self):
        return ('orbit_segment','variable','latitude','longitude')                

    def _shape(self):
        return (2,4,720,1440)

    def _variables(self):
        return ['mingmt','windspd','winddir','scatflag','radrain',
                'longitude','latitude','land','ice','nodata']

    # _default_get():
    
    def _get_index(self,var):
        return {'windspd' : 1,
                'winddir' : 2,
                'rain' : 3,
                }[var]

    def _get_scale(self,var):
        return {'mingmt' : 6.0,
                'windspd' : 0.2,
                'winddir' : 1.5,
                }[var]

    # _get_ attributes:

    def _get_long_name(self,var):
        return {'mingmt' : 'Minute of Day UTC',
                'windspd' : '10-m Surface Wind Speed',
                'winddir' : '10-m Surface Wind Direction',
                'scatflag' : 'Scatterometer Rain Flag',
                'radrain' : 'Radiometer Rain Flag',
                'longitude' : 'Grid Cell Center Longitude',
                'latitude' : 'Grid Cell Center Latitude',
                'land' : 'Is this land?',
                'ice' : 'Is this ice?',
                'nodata' : 'Is there no data?',
                }[var]

    def _get_units(self,var):
        return {'mingmt': 'minute of day',
                'windspd' : 'm/s',
                'winddir' : 'deg oceanographic',
                'scatflag' : '0=no-rain, 1=rain',
                'radrain' : '0=no-rain, -1=adjacent rain, >0=rain(km*mm/hr)',
                'longitude' : 'degrees east',
                'latitude' : 'degrees north',
                'land' : 'True or False',
                'ice' : 'True or False',
                'nodata' : 'True or False',
                }[var]

    def _get_valid_min(self,var):
        return {'mingmt' : 0.0,
                'windspd' : 0.0,
                'winddir' : 0.0,
                'scatflag' : 0,
                'radrain' : -1,
                'longitude' : 0.0,
                'latitude' : -90.0,
                'land' : False,
                'ice' : False,
                'nodata' : False,
                }[var]

    def _get_valid_max(self,var):
        return {'mingmt' : 1440.0,
                'windspd' : 50.0,
                'winddir' : 360.0,
                'scatflag' : 1,
                'radrain' : 31,
                'longitude' : 360.0,
                'latitude' : 90.0,
                'land' : True,
                'ice' : True,
                'nodata' : True,
                }[var]

    # _get_ variables:

    def _get_mingmt(self,var,bmap):
        mingmt = get_data(bmap,indx=0)
        mingmt *= self._get_scale(var)
        return mingmt

    def _get_scatflag(self,var,bmap):
        indx = self._get_index('rain')
        scatflag = get_data(ibits(bmap,ipos=0,ilen=1),indx=indx)
        bad = is_bad(get_data(bmap,indx=0))
        scatflag[bad] = self.missing
        return scatflag

    def _get_radrain(self,var,bmap):
        indx = self._get_index('rain')
        radrain = get_data(ibits(bmap,ipos=1,ilen=1),indx=indx)        
        good = (radrain == 1)        
        radrain[~good] = self.missing
        intrain = get_data(ibits(bmap,ipos=2,ilen=6),indx=indx)
        nonrain = where(intrain == 0)
        adjrain = where(intrain == 1)
        hasrain = where(intrain > 1)
        intrain[nonrain] = 0.0
        intrain[adjrain] = -1.0
        intrain[hasrain] = 0.5*(intrain[hasrain]-1)
        radrain[good] = intrain[good]
        bad = is_bad(get_data(bmap,indx=0))
        radrain[bad] = self.missing
        return radrain


class DailyVerify(Verify):
    """ Contains info for verification. """

    def __init__(self,dataset):
        self.filename = 'qscat_v4_daily_verify.txt'
        self.ilon1 = 170
        self.ilon2 = 175
        self.ilat1 = 274
        self.ilat2 = 278        
        self.iasc = 1
        self.variables = ['mingmt','windspd','winddir','scatflag','radrain']
        self.startline = 16                
        self.columns = {'mingmt' : 3,
                        'windspd' : 4,
                        'winddir' : 5,
                        'scatflag' : 6,
                        'radrain' : 7 }        
        Verify.__init__(self,dataset)


if __name__ == '__main__':
    """ Automated testing. """

    # read daily:    
    qscat = QuikScatDaily('qscat_20000111v4.gz')
    if not qscat.variables: sys.exit('file not found')
    
    # verify daily:
    verify = DailyVerify(qscat)
    if verify.success: print('successful verification for daily')
    else: sys.exit('verification failed for daily')
    print('')

    print('all tests completed successfully')
    print('')


try:
    import pyfits

except ImportError:
    import ds9_basic as _ds9

else:
    import ds9_pyfits as _ds9

ds9 = _ds9.ds9

#import sla
#import slav


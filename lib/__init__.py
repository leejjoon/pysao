from .version import __version__
from pysao.verbose import verbose

try:
    from .astropy_helper import pyfits

except ImportError:
    verbose.report("Loading pyfits failed. pysao.ds9 would not support fits-related tasks in this mode.", level="debug")
    import pysao.ds9_basic as _ds9

else:
    verbose.report("Loading pyfits succeded. pysao.ds9 will support fits-related tasks.", level="debug")
    import pysao.ds9_pyfits as _ds9

ds9 = _ds9.ds9

#import sla
#import slav

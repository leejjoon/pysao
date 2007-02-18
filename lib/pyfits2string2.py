import pyfits
import StringIO

class _File(pyfits.core._File):
    """A file I/O class"""

    def __init__(self, opened_file):
        self.name = None
        self.mode = "write"
        self.memmap = 0

        self.__file = opened_file
        self._size = 0

    def close():
        pass

import numpy

class ndarray(numpy.ndarray):
    def tofile(self, f):
        f.write(self.tostring())

def toString(hdu):
    fs = StringIO.StringIO()
    ff = _File(fs)
    hdu.data = ndarray(hdu.data)
    ff.writeHDU(hdu)

    fs.close()

    return fs

    
def test():
    #f = open("ttt.fits","w")
    f2 = pyfits.open("test1.fits")
    
    s = toString(f2[0])
    f.write(s)
    f.close()
    

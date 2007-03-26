

########## TODO
### *. think about the panto_wcs interface





# try to import pyfits pyfits2sting function.
# disaply fits directly is not supported if failed.

_pyfits2string = None

import pyfits

Card = pyfits.Card

if hasattr(pyfits, "padLength"):
    padLength = pyfits.padLength
elif hasattr(pyfits, "_padLength"):
    padLength = pyfits._padLength
elif hasattr(pyfits.core, "_padLength"):
    padLength = pyfits.core._padLength
else:
    raise ImportError

if hasattr(pyfits, "ImageBaseHDU"):
    ImageBaseHDU = pyfits.ImageBaseHDU
elif hasattr(pyfits, "_ImageBaseHDU"):
    ImageBaseHDU = pyfits._ImageBaseHDU
elif hasattr(pyfits.core, "_ImageBaseHDU"):
    ImageBaseHDU = pyfits.core._ImageBaseHDU
else:
    raise ImportError

def _pad(input):
    """Pad balnk space to the input string to be multiple of 80."""
    _len = len(input)
    if _len == Card.length:
        return input
    elif _len > Card.length:
        strlen = _len % Card.length
        if strlen == 0:
            return input
        else:
            return input + ' ' * (Card.length-strlen)

    # minimum length is 80
    else:
        strlen = _len % Card.length
        return input + ' ' * (Card.length-strlen)
    
# for recent version of python
def _pyfits2string(hdu):
    """ convert fits HDU into string"""

    hdu.update_header()
    
    blocks = []
    blocks.append( repr(hdu.header.ascard) + _pad('END') )
    blocks.append( padLength(len(blocks[0]))*' ')

    if hdu.data is not None:

        # if image, need to deal with byte order
        if isinstance(hdu, ImageBaseHDU):
            #output = hdu.data.newbyteorder('big')

            if 1: #numpy
                dt = hdu.data.dtype.newbyteorder(">")
                output = hdu.data.astype(dt)

            #print output.dtype.byteorder
            #if hdu.data.dtype.base.byteorder == "<":
            #    output = hdu.data.byteswap(False) # False : returns copy
            ##elif hdu.data.dtype.byteorder == ">":
            #else:
            #    output = hdu.data

        else:
            raise "input should be an instance of ImageBaseHDU"

        blocks.append( output.tostring() )
        #_size = output.nelements() * output._itemsize
        _size = output.nbytes

        # pad the FITS data block
        if _size > 0:
            blocks.append(padLength(_size)*'\0')

    return "".join(blocks)

       

import re

wcs_key_pattern = re.compile(r'^(NAXIS|CD|CDELT|CRPIX|CRVAL|CTYPE|LONGPOLE|LATPOLE|PV2|DISTORT|OBJECT|BUNIT)')

def get_wcs_headers(h):
    """ gien fits header, select only wcs related items and return them
    in a single string"""
    
    cardlist = h.ascardlist()
    l =[s.ascardimage() for s in cardlist if wcs_key_pattern.match(s.key)]

    return "\n".join(l)



import ds9_basic

import funtools

class ds9(ds9_basic.ds9):


    def view(self, img, header=None, frame=None, asFits=False):
        """ Display image which can be either numarray instance
        or pyfits HDU
        """

        _frame_num = self.frame()

        try:
            if frame:
                self.frame(frame)
            
            if isinstance(img, ImageBaseHDU):
                if asFits:
                    self.view_fits(img)
                else:
                    if not header:
                        header = img.header
                    self.view_array(img.data, header)
            else:
                self.view_array(img, header)

        finally:
            self.frame(_frame_num)
            

    def view_array(self, img, header=None):
        super(ds9, self).view_array(img)
        
        if header:
            self.set("wcs replace", get_wcs_headers(header))
        

    def view_fits(self, hdu):
        try:
            hdu.data.shape = hdu.data.shape[-2:]
        except ValueError:
            raise "unsupported array shape : %s" % repr(hdu.data.shape)
        #if len(hdu.data.shape) != 2:
        #    raise "Only 2-d image is supported. %s", im.shape

        s = _pyfits2string(hdu)
    
        self.set("fits", s)
        
            
    def panto(self, coord): # ra, dec
        """ra, dec in degree"""
        self.set("pan to %10.8f %10.8f wcs fk5" % coord.fk5()) # (ra, dec))

    def panto_wcs(self, coord): # ra, dec
        """ra, dec in degree"""
        self.set("pan to %10.8f %10.8f wcs fk5" % coord.fk5()) # (ra, dec))

    def mask_from_curent_region(self):
        shape = map(int, self.get("fits size").split())
        reg = self.get("regions")

        m = funtools.make_mask_from_region((shape[1], shape[0]), reg)
        return m
        

def test():

    dds9 = ds9()
    import time
    time.sleep(1)
    d = reshape(numpy.arange(100), (10,10))
    dds9.view(d)
    time.sleep(1)
    
    t_fits_name = os.path.join(dds9._tmpd_name, "test.fits")
    open(t_fits_name, "w").write(ds9_basic._ds9_python_logo)

    try:
        f = pyfits.open(t_fits_name)
        dds9.view(f[0])
        dds9.view(f[0], asFits=True)
    finally:
        os.remove(t_fits_name)
    
    del dds9

if __name__ == "__main__":
    test()

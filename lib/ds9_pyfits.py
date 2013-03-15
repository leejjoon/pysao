

########## TODO
### *. think about the panto_wcs interface




from .astropy_helper import pyfits
from pysao.pyfits2string import fits2string


import re

# LTV,LTV seems to be related with physical coordinates
# DTV, DTM?

wcs_key_pattern = re.compile(r'^(NAXIS|CD|CDELT|CRPIX|CRVAL|CTYPE|CROTA|LONGPOLE|LATPOLE|PV|DISTORT|OBJECT|BUNIT|EPOCH|EQUINOX|LTV|LTM|DTV|DTM)')

def get_wcs_headers(h):
    """
    given a fits header, select only wcs related items and return them
    in a single string
    """

    cardlist = h.ascardlist()
    l =[s.ascardimage() for s in cardlist if wcs_key_pattern.match(s.key)]

    return "\n".join(l)



import pysao.ds9_basic as ds9_basic

class ds9(ds9_basic.ds9):


    def view(self, img, header=None, frame=None, asFits=True):
        """
        Display image which can be either numarray instance
        or pyfits HDU
        """

        _frame_num = self.frame()

        try:
            if frame:
                self.frame(frame)

            if isinstance(img, pyfits.ImageHDU) or isinstance(img, pyfits.PrimaryHDU):
                if asFits:
                    self.view_fits(img)
                else:
                    if not header:
                        header = img.header
                    self.view_array(img.data, header)
            else:
                if header is not None and asFits:
                    hdu=pyfits.ImageHDU(img, header)
                    self.view_fits(hdu)
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

        s = fits2string(hdu)

        self.set("fits", s)


    def panto(self, coord): # ra, dec
        """ra, dec in degree"""
        self.set("pan to %10.8f %10.8f wcs fk5" % coord.fk5()) # (ra, dec))

    def panto_wcs(self, coord): # ra, dec
        """ra, dec in degree"""
        self.set("pan to %10.8f %10.8f wcs fk5" % coord.fk5()) # (ra, dec))



def test():

    dds9 = ds9()
    import time
    time.sleep(1)
    d = reshape(numpy.arange(100), (10,10))
    dds9.view(d)
    time.sleep(1)

    t_fits_name = os.path.join(dds9._tmpd_name, "test.fits")
    open(t_fits_name, "w").write(ds9_basic._ds9_python_logo)

    from .astropy_helper import pyfits

    try:
        f = pyfits.open(t_fits_name)
        dds9.view(f[0])
        dds9.view(f[0], asFits=True)
    finally:
        os.remove(t_fits_name)

    del dds9

if __name__ == "__main__":
    test()

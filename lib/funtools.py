import pyfits
import numpy
import os
import os.path

class WrongImageShape(Exception):
    pass

def make_mask_from_region(img, region, header=None):
    """ image : numarray image
        region : region description in image coordinate """
    
    hdul = pyfits.HDUList()
    hdu = pyfits.PrimaryHDU()
    if header:
        # copying the header is necessary because
        # writeto method can modify the header.
        
        hdu.header = header.copy()
    if hasattr(img, "shape"):
        shape = img.shape
    elif isinstance(img, tuple):
        shape = img
    else:
        raise WrongImageShape("needs two dimensional array")
        
    hdu.data = numpy.ones(shape[-2:], dtype=numpy.uint8)
    hdu.update_header()
    hdul.append(hdu)

    from tempfile import mkdtemp
    temp_path = mkdtemp()

    fitsname = os.path.join(temp_path, "tmp.fits")
    regname = os.path.join(temp_path, "tmp.reg")
    maskname = os.path.join(temp_path, "mask.fits")
    #maskname = "./mask.fits"

    import shutil
    try:
        hdul.writeto(fitsname)
        open(regname, "w").write(region)

        os.system("funimage %s[@%s] %s" % (fitsname, regname, maskname))
        mask = pyfits.open(maskname)[0].data
    finally:
        shutil.rmtree(temp_path)

    # Work-around for some bug???
    m = mask.astype(numpy.bool8)
    ny, nx = m.shape
    for iy in range(ny):
        if numpy.alltrue(m[iy,:]):
            m[iy,:] = False

    return m




def mask_from_region(fitsname, region_string):

    temp_path = mkdtemp()

    regname = os.path.join(temp_path, "tmp.reg")
    maskname = os.path.join(temp_path, "mask.fits")

    try:
        open(regname, "w").write(region_string)

        os.system("funimage %s[@%s] %s" % (fitsname, regname, maskname))
        mask = pyfits.open(maskname)[0].data
    finally:
        shutil.rmtree(temp_path)

    return mask



def ds9_get_mask_from_current_region(ds9):
    shape = map(int, ds9.get("fits size").split())
    reg = ds9.get("regions -format ds9 -system image")

    m = make_mask_from_region((shape[1], shape[0]), reg)
    return m


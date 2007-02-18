import pyfits
import numpy

def make_mask_from_region(img, region, header=None):
    """ image : numarray image
        region : region description in image coordinate """
    
    hdul = pyfits.HDUList()
    hdu = pyfits.PrimaryHDU()
    if header:
        hdu.header = header
    if hasattr(img, "shape"):
        shape = img.shape
    elif isinstance(img, tuple):
        shape = img
    else:
        raise "img (1st argument) must be shape (tuple) of image"
        
    hdu.data = numpy.ones(shape[-2:], dtype=numpy.uint8)
    hdul.append(hdu)

    from tempfile import mkdtemp
    temp_path = mkdtemp()

    fitsname = temp_path+"/tmp.fits"
    regname = temp_path+"/tmp.reg"
    maskname = temp_path+"/mask.fits"
    #maskname = "./mask.fits"

    import os
    try:
        hdul.writeto(fitsname)
        open(regname, "w").write(region)

        os.system("funimage %s[@%s] %s" % (fitsname, regname, maskname))
        mask = pyfits.open(maskname)[0].data
    finally:
        import shutil
        shutil.rmtree(temp_path)

    m = mask.astype(numpy.bool8)
    ny, nx = m.shape
    for iy in range(ny):
        if numpy.alltrue(m[iy,:]):
            m[iy,:] = False

    return m


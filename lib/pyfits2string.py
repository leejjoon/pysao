


# try to import pyfits pyfits2sting function.
# disaply fits directly is not supported if failed.

import pyfits

Card = pyfits.Card

if hasattr(pyfits, "padLength"):
    padLength = pyfits.padLength
elif hasattr(pyfits, "_padLength"):
    padLength = pyfits._padLength
elif hasattr(pyfits.core, "_padLength"):
    padLength = pyfits.core._padLength
elif hasattr(pyfits.core, "_padLength"):
    padLength = pyfits.core._padLength
elif hasattr(pyfits.util, "_pad_length"):
    padLength = pyfits.util._pad_length
else:
    raise ImportError

if hasattr(pyfits, "ImageBaseHDU"):
    ImageBaseHDU = pyfits.ImageBaseHDU
elif hasattr(pyfits, "_ImageBaseHDU"):
    ImageBaseHDU = pyfits._ImageBaseHDU
elif hasattr(pyfits.core, "_ImageBaseHDU"):
    ImageBaseHDU = pyfits.core._ImageBaseHDU
elif hasattr(pyfits.hdu.image, "_ImageBaseHDU"):
    ImageBaseHDU = pyfits.hdu.image._ImageBaseHDU
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
    
def fits2string(hdu):
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


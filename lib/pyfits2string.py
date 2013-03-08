


# try to import pyfits pyfits2sting function.
# disaply fits directly is not supported if failed.

import pyfits

Card = pyfits.Card


# copied from pyftis/util.py
BLOCK_SIZE = 2880 # the FITS block size
def _pad_length(stringlen):
    """Bytes needed to pad the input stringlen to the next FITS block."""

    return (BLOCK_SIZE - (stringlen % BLOCK_SIZE)) % BLOCK_SIZE

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
            return input + b' ' * (Card.length-strlen)

    # minimum length is 80
    else:
        strlen = _len % Card.length
        return input + b' ' * (Card.length-strlen)
    
def fits2string(hdu):
    """ convert fits HDU into string"""

    hdu.update_header()
    
    blocks = []
    blocks.append( repr(hdu.header.ascard).encode() + _pad(b'END') )
    blocks.append( _pad_length(len(blocks[0]))*b' ')

    if hdu.data is not None:

        # if image, need to deal with byte order
        if isinstance(hdu, pyfits.ImageHDU) or isinstance(hdu, pyfits.PrimaryHDU):
            dt = hdu.data.dtype.newbyteorder(">")
            output = hdu.data.astype(dt)

        else:
            raise ValueError("input should be an instance of ImageHDU or PrimaryHDU")

        blocks.append( output.tostring() )
        _size = output.nbytes

        # pad the FITS data block
        if _size > 0:
            blocks.append(_pad_length(_size)*b'\0')

    return b"".join(blocks)


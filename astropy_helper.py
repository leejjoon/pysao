try:
    import astropy
except ImportError:
    has_astropy = False
else:
    has_astropy = True

if has_astropy:
    from astropy.io import fits as pyfits
else:
    import pyfits

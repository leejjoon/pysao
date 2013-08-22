pysao
=====

This project is aimed to provide a python interface for some programs
developed by Smithsonian Astrophysical Observatory(SAO). One of the
main goal is to communicate with ds9 from python shell via the XPA
protocol. It provides a python wrapper for subset of XPA library and
python module for ds9 based on the XPA module.

Homepage : http://leejjoon.github.com/pyregion/

pyregion is "easy_install"able.

http://pypi.python.org/pypi/pysao

```
pip install pysao
```

USAGE
=====


```python
>>> import pysao

# run new instance of ds9
>>> ds9 = pysao.ds9()

>>> import numpy
>>> im = numpy.reshape(numpy.arange(100), (10, 10))
# display 2-d array
>>> ds9.view(im)



>>> import pyfits
>>> f = pyfits.open('test.fits')
# display first extension of fits file
>>> ds9.view(f[0])

# access with XPA method. 
>>> ds9.set('file test.fits')
>>> ds9.get('file')

# list available xpa commands
>>> ds9.xpa_help()

# help on the specific xpa command
>>> ds9.xpa_help("tile")
```


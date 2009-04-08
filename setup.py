from distutils.core import setup
from distutils.extension import Extension

import sys
 

def main():
    #dolocal()
    setup(name = "pysao",
          version = "0.1b1",
          description = "python wrapper around some SAO tools",
          author = "Jae-Joon Lee",
          author_email = "lee.j.joon@gmail.com",
          maintainer_email = "lee.j.joon@gmail.com",
          url = "",
          license = "MIT",
          platforms = ["Linux","Mac OS X"], # "Solaris"?
          packages = ['pysao'],
          package_dir={'pysao':'lib'},
          #package_data={'pysao': ["ds9_xpa_help.pickle"]},
          
          ext_modules=[ Extension("pysao.xpa",       ["xpa.c"],
                                  include_dirs=['./xpalib'],
                                  library_dirs=['./xpalib'],
                                  libraries=['xpa']),
                        ],
          )

if __name__ == "__main__":
    main()

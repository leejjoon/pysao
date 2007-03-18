from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

import sys
 
if not hasattr(sys, 'version_info') or sys.version_info < (2,3,0,'alpha',0):
    raise SystemExit, "Python 2.3 or later required to build pysao."

def dolocal():
    """Adds a command line option --local=<install-dir> which is an abbreviation for
    'put all of pyfits in <install-dir>/pyfits'."""
    if "--help" in sys.argv:
        print >>sys.stderr
        print >>sys.stderr, " options:"
        print >>sys.stderr, "--local=<install-dir>    same as --install-lib=<install-dir>"
    for a in sys.argv:
        if a.startswith("--local="):
            dir = a.split("=")[1]
            sys.argv.extend([
                "--install-lib="+dir,
                ])
            sys.argv.remove(a)

def main():
    dolocal()
    setup(name = "pysao",
          version = "0.1b1",
          description = "General Use Python Tools",
          author = "Jae-Joon Lee",
          maintainer_email = "lee.j.joon@gmail.com",
          license = "???",
          platforms = ["Linux","Solaris","Mac OS X"],
          packages = ['pysao'],
          package_dir={'pysao':'lib'},
          ext_modules=[ Extension("xpa",       ["xpa.pyx"],
                                  include_dirs=['/Users/jjlee/local/src/xpalib/xpa-2.1.6'],
                                  library_dirs=['/Users/jjlee/local/src/xpalib/xpa-2.1.6'],
                                  libraries=['xpa']),
                        ],
          cmdclass = {'build_ext': build_ext},
          #test_suite = "test.saods9_test",
          )

if __name__ == "__main__":
    main()

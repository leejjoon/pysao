from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, Extension

# check if cython or pyrex is available.
pyrex_impls = 'Cython.Distutils.build_ext', 'Pyrex.Distutils.build_ext'
for pyrex_impl in pyrex_impls:
    try:
        # from (pyrex_impl) import build_ext
        build_ext = __import__(pyrex_impl, fromlist=['build_ext']).build_ext
        break
    except:
        pass

if 'build_ext' in globals(): # pyrex or cython installed
    PYREX_SOURCE = "xpa.pyx"
else:
    PYREX_SOURCE = "xpa.c"
    from setuptools.command.build_ext import build_ext

import os.path
XPALIB_DIR = "xpa-2.1.14"
CONF_H_NAME = os.path.join(XPALIB_DIR, "conf.h")

class build_ext_with_configure( build_ext ):
    def build_extensions(self):
        import subprocess
        if not os.path.exists(CONF_H_NAME):
            subprocess.check_call(["sh", "./configure"],
                                  cwd=XPALIB_DIR)
        build_ext.build_extensions(self)

from distutils.command.clean import clean as _clean
class clean( _clean ):
    def run(self):
        import subprocess
        subprocess.call(["make", "-f", "Makefile", "clean"],
                        cwd=XPALIB_DIR)
        if os.path.exists(CONF_H_NAME):
            os.remove(CONF_H_NAME)
        _clean.run(self)

xpalib_files = """acl.c
                  client.c
                  clipboard.c
                  command.c
                  find.c
                  port.c
                  remote.c
                  tcp.c
                  timedconn.c
                  word.c
                  xalloc.c
                  xlaunch.c
                  xpa.c
                  xpaio.c
                  """.split()

xpa_sources = [PYREX_SOURCE]  + [os.path.join(XPALIB_DIR, c) \
                                 for c in xpalib_files]

xpalib_defines  = [("HAVE_CONFIG_H", "1")]

for line in open('lib/version.py').readlines():
    if (line.startswith('__version__')):
        exec(line.strip())


def main():
    #dolocal()

    setup(name = "pysao",
          version = __version__,
          description = "python wrapper around SAO XPA and DS9",
          author = "Jae-Joon Lee",
          author_email = "lee.j.joon@gmail.com",
          maintainer_email = "lee.j.joon@gmail.com",
          url = "http://github.com/leejjoon/pysao",
          license = "MIT",
          platforms = ["Linux","Mac OS X"], # "Solaris"?
          packages = ['pysao'],
          package_dir={'pysao':'lib'},
          #package_data={'pysao': ["ds9_xpa_help.pickle"]},

          ext_modules=[ Extension("pysao.xpa", xpa_sources,
                                  include_dirs=[XPALIB_DIR],
                                  define_macros=xpalib_defines,
                                  depends=[CONF_H_NAME],
                                  ),
                        ],
          cmdclass = {'build_ext': build_ext_with_configure,
                      'clean': clean},
          #use_2to3 = True,
          classifiers=['Development Status :: 5 - Production/Stable',
                       'Intended Audience :: Science/Research',
                       'License :: OSI Approved :: MIT License',
                       'Operating System :: MacOS :: MacOS X',
                       'Operating System :: POSIX :: Linux',
                       'Programming Language :: Cython',
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'Topic :: Scientific/Engineering :: Astronomy',
                       ]
          )

if __name__ == "__main__":
    main()

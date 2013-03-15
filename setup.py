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

xpalib_defines  = [(s, "1") for s in """HAVE_STRING_H
                                        HAVE_STDLIB_H
                                        HAVE_MALLOC_H
                                        HAVE_UNISTD_H
                                        HAVE_GETOPT_H
                                        HAVE_MEMCPY
                                        HAVE_PWD_H
                                        HAVE_VALUES_H
                                        HAVE_DLFCN_H
                                        HAVE_SYS_UN_H
                                        HAVE_SYS_SHM_H
                                        HAVE_SYS_MMAN_H
                                        HAVE_SYS_IPC_H
                                        HAVE_SETJMP_H
                                        HAVE_SOCKLEN_T
                                        HAVE_STRCHR
                                        HAVE_MEMCPY
                                        HAVE_SNPRINTF
                                        HAVE_SETENV""".split()]


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
                                  define_macros = xpalib_defines,
                                  #library_dirs=[XPALIB_DIR],
                                  #libraries=['xpa']
                                  ),
                        ],
          cmdclass = {'build_ext': build_ext},
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

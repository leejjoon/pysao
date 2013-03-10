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
XPALIB_DIR = "xpa-2.1.13"

xpalib_files = """xpa.c
                  xpaio.c
                  command.c
                  acl.c
                  remote.c
                  clipboard.c
                  port.c
                  tcp.c
                  client.c
                  word.c
                  xalloc.c
                  find.c
                  xlaunch.c
                  timedconn.c
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



def main():
    #dolocal()
    setup(name = "pysao",
          version = "0.1b2",
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

          ext_modules=[ Extension("pysao.xpa", xpa_sources,
                                  include_dirs=[XPALIB_DIR],
                                  define_macros = xpalib_defines,
                                  #library_dirs=[XPALIB_DIR],
                                  #libraries=['xpa']
                                  ),
                        ],
          cmdclass = {'build_ext': build_ext},
          #use_2to3 = True,
          )

if __name__ == "__main__":
    main()

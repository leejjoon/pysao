from distutils.core import setup

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

from distutils.extension import Extension

import sys
 
if sys.version_info[0] >= 3:
    #import multiprocessing
    #from distutils import util
    def refactor(x):
        from lib2to3.refactor import RefactoringTool, get_fixers_from_package
        class DistutilsRefactoringTool(RefactoringTool):
            def ignore(self, msg, *args, **kw):
                pass
            log_error = log_message = log_debug = ignore
        fixer_names = get_fixers_from_package('lib2to3.fixes')
        r = DistutilsRefactoringTool(fixer_names, options=None)
        r.refactor([x], write=True)

    original_build_py = build_py
    class build_py(original_build_py):
        def run_2to3(self, files):
            # We need to skip certain files that have already been
            # converted to Python 3.x
            filtered = [x for x in files if 'py3' not in x]
            if sys.platform.startswith('win'):
                # doing this in parallel on windows may crash your computer
                [refactor(f) for f in filtered]
            else:
                [refactor(f) for f in filtered]
                #p = multiprocessing.Pool()
                #p.map(refactor, filtered)

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
          cmdclass={'build_py':build_py},
          #package_data={'pysao': ["ds9_xpa_help.pickle"]},
          
          ext_modules=[ Extension("pysao.xpa",       ["xpa.c"],
                                  include_dirs=['./xpalib'],
                                  library_dirs=['./xpalib'],
                                  libraries=['xpa']),
                        ],
          )

if __name__ == "__main__":
    main()

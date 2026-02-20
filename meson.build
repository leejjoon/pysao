project('pysao', 'c', 'cython',
  version: '1.0.1',
  meson_version: '>=0.64.0'
)

py_mod = import('python')
py = py_mod.find_installation(pure: false)
py_dep = py.dependency()

xpa_dir = 'xpa-2.1.14'

# Configure XPA (equivalent to build_ext_with_configure in setup.py)
# We check if conf.h exists, if not run configure.
# In Meson, it's often better to let Meson handle configuration, 
# but for a bundled library like XPA, running its own configure is sometimes easier.
# However, we can also just define the macros manually if we know them.
# The setup.py used: define_macros=[("HAVE_CONFIG_H", "1")]

xpa_sources = files(
  xpa_dir / 'acl.c',
  xpa_dir / 'client.c',
  xpa_dir / 'clipboard.c',
  xpa_dir / 'command.c',
  xpa_dir / 'find.c',
  xpa_dir / 'port.c',
  xpa_dir / 'remote.c',
  xpa_dir / 'tcp.c',
  xpa_dir / 'timedconn.c',
  xpa_dir / 'word.c',
  xpa_dir / 'xalloc.c',
  xpa_dir / 'xlaunch.c',
  xpa_dir / 'xpa.c',
  xpa_dir / 'xpaio.c'
)

# Run configure if conf.h is missing
fs = import('fs')
if not fs.exists(xpa_dir / 'conf.h')
  run_command('sh', '-c', 'cd ' + (meson.current_source_dir() / xpa_dir) + ' && ./configure', check: true)
endif

pysao_xpa = py.extension_module(
  'xpa',
  'xpa.pyx',
  xpa_sources,
  include_directories: [xpa_dir],
  dependencies: [py_dep],
  c_args: ['-DHAVE_CONFIG_H=1'],
  subdir: 'pysao',
  install: true
)

# Install Python files
py_sources = [
  'lib/__init__.py',
  'lib/astropy_helper.py',
  'lib/displaydev_lite.py',
  'lib/ds9_basic.py',
  'lib/ds9_pyfits.py',
  'lib/ds9_xpa_help.py',
  'lib/parse_xpahtml.py',
  'lib/pyfits2string.py',
  'lib/PylabBlockingInput.py',
  'lib/verbose.py',
  'lib/version.py',
  'lib/xpa_wrap.py',
]

py.install_sources(
  py_sources,
  subdir: 'pysao'
)

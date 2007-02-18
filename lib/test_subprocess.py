from subprocess import Popen
import os

tmpdir = "/tmp/jjjjj"
env = os.environ.copy()
env["XPA_TMPDIR"] = tmpdir

import os

p = Popen("ds9 -xpa local -xpa noxpans  &", shell=True, env=env)
#p = Popen("ds9 -xpa local &", shell=False, env=env)
sts = os.waitpid(p.pid, 0)

os.listdir(tmpdir)

import ds9_xpa_help
import os.path
import pickle

class Invalid_Ds9_Xpa_command:
    pass

_pkl_name = os.path.join(os.path.dirname(ds9_xpa_help.__file__),
                         "ds9_xpa_help.pickle")

_pkl = pickle.load(open(_pkl_name))

def help(xpa_command=None):

    if xpa_command is None:
        _help_summary()
    else:
        _help_command(xpa_command)

def _help_summary():
    xpa_command_names = _pkl.keys()
    xpa_command_names.sort()

    for comm in xpa_command_names:
        sd = _pkl[comm]["short_expl"]
        #if len(sd) > 60:
        #    sd = sd[:60] + "..."
        print "[%s] %s" % (comm, sd)

def _help_command(xpa_command_name):
    if xpa_command_name not in _pkl:
        raise Invalid_Ds9_Xpa_command()

    print _pkl[xpa_command_name]["expl"]
    print
    print _pkl[xpa_command_name]["syntax"]

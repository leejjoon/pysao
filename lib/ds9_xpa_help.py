import os
import tempfile

class Invalid_Ds9_Xpa_command:
    pass


__help_dict = {}


_get_xpahelp_tcl_source_tmpl = """

    set tc [open $ds9(root)/doc/ref/xpa.html]
    set xpastr [read $tc]
    close $tc
    unset tc

    set tc [open %s "w"]
    puts  $tc $xpastr
    close $tc
    unset tc
    unset xpastr

"""

def get(ds9):
    return get_from_zip(ds9)


def get_from_tcl(ds9):
    ver = ds9._ds9_version
    if ver not in __help_dict:
        tmpdir = ds9._tmpd_name

        # couldn't figure out easy way to receive a string from Tcl
        # without using a temporary file.
        # Can be done by defining an XPA commmand but seems to be an overkill.

        html_name = tmpdir + "/temp_for_helpfile"

        f = tempfile.NamedTemporaryFile(dir=tmpdir, suffix=".tcl")
        f.write(_get_xpahelp_tcl_source_tmpl % (html_name))
        f.flush()

        ds9.set("source %s" % (f.name))
        f.close()

        s = open(html_name).read()
        os.remove(html_name)

        __help_dict[ver] = ds9_help(s)

    return __help_dict[ver]

def get_from_zip(ds9):
    ver = ds9._ds9_version
    if ver not in __help_dict:
        path = ds9.path
        import zipfile
        zf = zipfile.ZipFile(path)
        for n in zf.namelist():
            if n.endswith("xpa.html"):
                break
        else:
            raise RuntimeError("couldn't find xpa.html with in the executable")

        html = zf.read(n)

        __help_dict[ver] = ds9_help(html)

    return __help_dict[ver]


import parse_xpahtml

class ds9_help(object):
    def __init__(self, html_string):
        self._help_data = parse_xpahtml.parse_xpa_help(html_string)

    def __call__(self, xpa_command=None):

        if xpa_command is None:
            self._help_summary()
        elif xpa_command == "ALL":
            self._help_all()
        else:
            self._help_command(xpa_command)

    def _help_summary(self):
        xpa_command_names = sorted(self._help_data.keys())

        for comm in xpa_command_names:
            expl = self._help_data[comm]["expl"]
            sd = expl.split(".")[0].strip()
            print "[%s] %s" % (comm, sd)

    def _help_all(self):
        xpa_command_names = sorted(self._help_data.keys())

        for comm in xpa_command_names:
            print "[%s]" % (comm)
            self._help_command(comm)

    def _help_command(self, xpa_command_name):
        if xpa_command_name not in self._help_data:
            raise Invalid_Ds9_Xpa_command()

        print ""
        print self._help_data[xpa_command_name]["expl"]
        print "<Syntax>"
        print self._help_data[xpa_command_name]["syntax"]
        print "<Example>"
        print self._help_data[xpa_command_name]["example"]

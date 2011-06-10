
import os
import time
#from sets import Set
import weakref

import displaydev_lite as displaydev


import pysao.xpa as xpa
import pysao.ds9_xpa_help as ds9_xpa_help
from pysao.verbose import verbose

class UnsupportedDatatypeException(Exception):
    pass

class UnsupportedImageShapeException(Exception):
    pass


from subprocess import Popen
#import os.path

import numpy

from tempfile import mkdtemp

def _find_ds9():
    path="ds9"
    for dirname in os.getenv("PATH").split(":"):
        possible = os.path.join(dirname, path)
        if os.path.isfile(possible):
            return possible

def _extract_xpa_html(path):
    import zipfile
    ds9_zip = zipfile.ZipFile(path)
    for zf in ds9_zip.namelist():
        if zf.endswith("xpa.html"):
            return ds9_zip.read(zf)

    raise RuntimeError("No ds9 is found in your path.")


class ds9(object):

    # _ImgCode : borrowed from pyfits
    _ImgCode = {'float32': -32,
                'float64': -64,
                'int16': 16,
                'int32': 32,
                'int64': 64,
                'uint8': 8}

    _tmp_dir_list = set()
    _ds9_instance_list = []

    @classmethod
    def _purge_tmp_dirs(cls):
        """
        When used with ipython (pylab mode), it seems that the objects
        are not prperly deleted, i.e., temporary directories are not
        deleted. This is a work around for that.
        """
        import shutil
        for tds9_ref in cls._ds9_instance_list:
            verbose.report("purging remaning ds9 instances", "debug")
            tds9 = tds9_ref()
            if tds9 is not None:
                verbose.report("deleting  ds9", "debug")
                tds9._purge()

        if cls._tmp_dir_list:
            verbose.report("purging remaning temporary dirs", "debug")
            for d in cls._tmp_dir_list:
                shutil.rmtree(d)


    def __init__(self, path=None, wait_time=10, quit_ds9_on_del=True,
                 load_help_file=True):
        """
        path :path of the ds9
        wait_time : waiting time before error is raised
        quit_ds9_on_del : If True, try to quit ds9 when this instance is deleted.
        """

        # determine whther to quit ds9 also when object deleted.
        self.quit_ds9_on_del = quit_ds9_on_del
        self._need_to_be_purged = False

        if path is None:
            self.path = _find_ds9()
        else:
            self.path = path

        xpa_name, ds9_unix_name = self.run_unixonly_ds9_v2(wait_time)
        try:
            xpa_name = xpa_name.encode()
        except AttributeError:
            pass
        self.xpa_name, self.ds9_unix_name = xpa_name, ds9_unix_name
        self.xpa = xpa.xpa(self.xpa_name)

        # numdisp setup
        numdisp_dev = "unix:%s" % self.ds9_unix_name
        self.numdisp_dev = numdisp_dev

        verbose.report("establish numdisplay connection (%s)" % (self.numdisp_dev,), level="debug")
        self.numdisp = displaydev.ImageDisplayProxy(self.numdisp_dev)

        self._ds9_version = self.get("version").strip()
        if load_help_file:
            self._helper = unicode(ds9_xpa_help.get(self))
        else:
            self._helper = None

        self._need_to_be_purged = True


    def __str__(self):
        pass

    def _purge(self):
        if not self._need_to_be_purged:
            return

        if not self.quit_ds9_on_del:
            verbose.report("You need to manually delete tmp. dir (%s)" % (self._tmpd_name), level="helpful")
            self._need_to_be_purged = False
            return

        if self.numdisp:
            self.numdisp.close()

        try:
            if self._ds9_process.poll() is None:
                self.set("quit")
        except xpa.XpaException, err:
            verbose.report("Warning : " + err.args[0])

        try:
            os.rmdir(self._tmpd_name)
            self._tmp_dir_list.remove(self._tmpd_name)
        except OSError:
            verbose.report("Warning : couldn't delete the temporary directory (%s)" % (self._tmpd_name,))
        else:
            verbose.report("temporary directory deleted", level="debug")

        self._need_to_be_purged = False


    def __del__(self):

        verbose.report("deleteing pysao.ds9", level="debug")
        self._purge()


    def show_logo(self):
        self.xpa.set("fits", _ds9_python_logo)


    def xpa_help(self, xpa_command=None):
        #ds9_xpa_help.help(xpa_command)
        self._helper(xpa_command)


    def run_unixonly_ds9_v2(self, wait_time):
        """ start ds9 """


        # when xpaname is parsed for local,
        # the prefix should match the XPA_TMPDIR
        # Hence, we create temporary dir under that directory.


        # The env variable "XPA_TMPDIR" is set to correct value when ds9 is
        # runned, and also xpa command is called (ie, python process).

        # This is a bit of problem when we have multiple instance of ds9.
        #env = os.environ.copy()
        env = os.environ

        self._tmpd_name = mkdtemp(prefix="xpa_"+env.get("USER",""),
                                  dir="/tmp")
        verbose.report("temporary directory created (%s)" % (self._tmpd_name,), level="debug")

        #print self._tmpd_name

        env["XPA_TMPDIR"] = self._tmpd_name

        iraf_unix = "%s/.IMT" % self._tmpd_name

        try:
            verbose.report("starting ds9 (path=%s)" % (self.path,), level="debug")
            #p = Popen(" ".join([self.path,
            #                    "-xpa local",
            #                    "-xpa noxpans",
            #                    "-unix_only",
            #                    "-unix %s &" % iraf_unix]),
            #          shell=True, env=env)
            p = Popen([self.path,
                       "-xpa", "local",
                       "-xpa", "noxpans",
                       "-unix_only",
                       "-unix",  "%s" % iraf_unix],
                      shell=False, env=env)

            #sts = os.waitpid(p.pid, 0)

            # wait until ds9 starts

            while wait_time > 0:
                file_list = os.listdir(self._tmpd_name)
                if len(file_list)>1:
                    #print file_list
                    break
                time.sleep(0.5)
                wait_time -= 0.5
            else:
                from signal import SIGTERM
                os.kill(p.pid, SIGTERM)
                raise OSError("Connection timeout with the ds9. Try to increase the *wait_time* parameter (current value is  %d s)" % (wait_time,))

        except:
            verbose.report("running  ds9 failed", level="debug")
            os.rmdir(self._tmpd_name)
            verbose.report("temporary directory deleted", level="debug")

            raise

        else:
            self._tmp_dir_list.add(self._tmpd_name)
            self._ds9_instance_list.append(weakref.ref(self))
            self._ds9_process = p

        file_list.remove(".IMT")
        xpaname = os.path.join(self._tmpd_name, file_list[0])

        env["XPA_TMPDIR"] = "/tmp/xpa" #self._tmpd_name

        return xpaname, iraf_unix


    def set_iraf_display(self):
        """
        Set the environemnt variable IMTDEV to the sokect address of
        the current pysao.ds9 instance. For example, your pyraf
        commands will use this ds9 for display.
        """
        os.environ["IMTDEV"] = "unix:%s" % (self.ds9_unix_name)


    def _check_ds9_process(self):
        ret = self._ds9_process.poll()
        if ret is not None:
            raise RuntimeError("The ds9 process is externally killed.")


    def set(self, param, buf=None):
        """
        XPA set method to ds9 instance

        set(param, buf=None)
        param : parameter string (eg. "fits" "regions")
        buf : aux data string (sometime string needed to be ended with CR)
        """
        self._check_ds9_process()
        try:
            param = param.encode()
        except AttributeError:
            pass

        self.xpa.set(param, buf)


    def get(self, param):
        """
        XPA get method to ds9 instance

        get(param)
        param : parameter string (eg. "fits" "regions")
        returns received string
        """
        self._check_ds9_process()
        try:
            param = param.encode()
        except AttributeError:
            pass
        return self.xpa.get(param)


    def view(self, img, header=None, frame=None, asFits=False):
        """
        Display numpy image
        """

        _frame_num = self.frame()

        try:
            if frame:
                self.frame(frame)

            self.view_array(img)

        except:
            self.frame(_frame_num)
            raise



    def view_array(self, img):

        img = numpy.array(img)
        if img.dtype.type == numpy.bool8:
            img = img.astype(numpy.uint8)

        try:
            img.shape = img.shape[-2:]
        except:
            raise UnsupportedImageShapeException, repr(img.shape)


        if img.dtype.byteorder in ["=", "|"]:
            dt=img.dtype.newbyteorder(">")
            img=numpy.array(img, dtype=dt)
            #img=img.astype(dt)
            byteorder=">"
        else:
            byteorder=img.dtype.byteorder

        endianness = {">":",arch=bigendian",
                      "<":",arch=littleendian"}[byteorder]
        #,
        #              "=":"",
        #              "|":""}

        (ydim, xdim) = img.shape
        arr_str = img.tostring()



        itemsize = img.itemsize * 8
        try:
            bitpix = self._ImgCode[img.dtype.name]

            #bitpix = pyfits.core._ImageBaseHDU.ImgCode[img.dtype.name]
        except KeyError, a:
            raise UnsupportedDatatypeException(a)


        #print endianness

        option = "[xdim=%d,ydim=%d,bitpix=%d%s]" % (xdim, ydim,
                                                    bitpix, endianness)

        self.set("array "+option, arr_str)



    def readcursor(self):
        """returns image coordinate postion, frame number, and key pressed"""
        r = self.numdisp.readCursor()
        x, y, f, k = r.strip().split()
        x, y = float(x), float(y)
        f = int(f)/100

        return x, y, f, k


    def mark(self, x, y, size, coord="image", group_name=None):

        if group_name is None:
            group_name = "_pyds9"

        try:
            _xysize = zip(x, y, size)
        except TypeError:
            _xysize = [x, y, size]

        def myregion(x, y, size, coord, tag):
            return "%s;circle(%10.8f,%10.8f,%10.8f) # tag={%s}" % \
                  (coord, x, y, size, tag)

        regions = [myregion(x1, y1, size1, coord, group_name) for x1, y1, size1 in _xysize]

        self.set_region("\n".join(regions + [""]))



    def load_region(self, region_name):
        #self.set_region(open(region_name).read())
        self.set("regions load %s" % region_name)


    def set_region(self, region_string):
        if region_string[-1] != "\n":
            region_string = region_string + "\n"

        self.set("regions", region_string)

    def frame(self, n=None):
        if n:
            self.set("frame %d" % n)
        else:
            return int(self.get("frame"))

    def load_fits(self, fname):
        self.set("file fits %s" % fname)

    def panto(self, x, y):
        self.panto_image(x, y)

    def panto_image(self, x, y):
        """x, y in image coord"""
        self.set("pan to %10.8f %10.8f image" % (x, y)) # (ra, dec))

    def zoomto(self, zoom):
        self.set("zoom to %e" % (zoom))


import atexit
atexit.register(ds9._purge_tmp_dirs)




def test():
    ds9 = ds9()
    import time
    time.sleep(1)
    d = reshape(numpy.arange(100), (10,10))
    ds9.view(d)
    time.sleep(1)
    del ds9


if __name__ == "__main__":
    test()



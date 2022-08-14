import os
import time
#from sets import Set
import weakref

import pysao.displaydev_lite as displaydev


#import pysao.xpa as xpa
import pysao.xpa_wrap as xpa
import pysao.ds9_xpa_help as ds9_xpa_help
from pysao.verbose import verbose as verbose

class UnsupportedDatatypeException(Exception):
    pass

class UnsupportedImageShapeException(Exception):
    pass


from subprocess import Popen
#import os.path

import numpy

from tempfile import mkdtemp
import shutil

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
                 load_help_file=True, **kwargs):
        """
        path :path of the ds9
        wait_time : waiting time before error is raised
        quit_ds9_on_del : If True, try to quit ds9 when this instance is deleted.

        Any additional keyword arguments will be passed a command 
        line arguments to execute ds9. For example,

            pysao.ds9(title="test")

        will add following arguments when executing the ds9.

            '-title test'

        """

        # determine whther to quit ds9 also when object deleted.
        self.quit_ds9_on_del = quit_ds9_on_del
        self._need_to_be_purged = False

        if path is None:
            self.path = _find_ds9()
        else:
            self.path = path

        self.xpa_name, self.ds9_unix_name = self.run_unixonly_ds9_v2(wait_time,
                                                                     kwargs)
        self.xpa = xpa.XPA(self.xpa_name)

        # numdisp setup
        self.numdisp_dev = "unix:%s" % self.ds9_unix_name

        verbose.report("establish numdisplay connection (%s)" % (self.numdisp_dev,), level="debug")
        self.numdisp = displaydev.ImageDisplayProxy(self.numdisp_dev)

        self._ds9_version = self.get("version").strip()
        if load_help_file:
            self._helper = ds9_xpa_help.get(self)
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
        except xpa.XpaException as err:
            verbose.report("Warning : " + err.message)

        try:
            shutil.rmtree(self._tmpd_name)
            #os.rmdir(self._tmpd_name)
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


    def run_unixonly_ds9_v2(self, wait_time, cmd_args_dict=None):
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

            cmd_args = ["-xpa", "local",
                        "-xpa", "noxpans",
                        "-unix_only",
                        "-unix",  "%s" % iraf_unix]

            for k, v in cmd_args_dict.items():
                cmd_args.extend(["-%s" % k, v])

            p = Popen([self.path] + cmd_args,
                      shell=False, env=env)

            #sts = os.waitpid(p.pid, 0)

            # wait until ds9 starts
            
            countdown = wait_time
            while countdown > 0:
                file_list = os.listdir(self._tmpd_name)
                if len(file_list)>1:
                    #print file_list
                    break
                time.sleep(0.5)
                countdown -= 0.5
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
        self.xpa.set(param, buf)


    def get(self, param):
        """
        XPA get method to ds9 instance

        get(param)
        param : parameter string (eg. "fits" "regions")
        returns received string
        """
        self._check_ds9_process()
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
            raise UnsupportedImageShapeException(repr(img.shape))


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
        except KeyError as a:
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


def _load_logo():
    _ds9_python_logo_text = r"""8dP08%a&)#!p)*!89##3-N**9&"*@#!J25#3&$JJN$*139K*8b!J)$dJN"3b)*!b6N&B59-a)#!p)*!5-cFi)*!b6N&B59-b)#!p)*!5-6B`)*!b3PT&8NmJ)#!p)*!0-#i`N!BJN$*#8d0"6%8J)$dJN!da,M#3"L#3-N4"9%&058iJ25#3$6!Z-*!')*!b4%&838e"@#!p)*!,-M8e,M#3"L#3JNK*8e428PNJ9%K*8b"'5946)%C*6%8J9d&6)%G&6N95394&4#"#@5"(58e3)&9658j()%C*9&059b#3Cd0268e&6P3J4QPdFe*A)'Pc)#K$+5"3CA4PFL",DA*MD'GPFh0ZCA)J+("PG'9b3'YTFQ0SCf9cFfjPFLjZCA3T,#"LGA3JBACKD@aKBQaP3dp068919#"eEQ4PFL"dD'8J4dj9)'GPEQ9bB@`JF(9LE'PM)'aTBf9ZBf8Z)*!M3dp068919#"'Eh)JFfpeFQ0PFb"cC@8JD(4dF$S[,hGhGbjVDA*MD'GPFh0ZCA)ZEQ9d)*"Y3dp068919#"*E@&RC5"dHA"P)(GTG'KTEL"(58e31L"(58e3Ae*(3Pp*68&(45#3)N0268e&6P3J8f9aG@9ZBf8JCQpb)%j"@%P6-b!J)$SJ8N9%,#"(8N9&6L`J3Na945#3F%914##3rb#3rb#3rb#3rb#3rb#38[q3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq30raj-B[krj$rrj"fq8dq9l,rN2rrN(INkZaRmIq3&IMSrj!4k2[rN!Iilqk3#1hmrj$rrj!mC-[rN"A3@Iq3$IVVrreTb2q3"[0RBR0cFh"F2$Be00ErN2rrN#l8YlCrHAUVm2q3"NClrj!9`acrN!frD[[k@T,rN!E)+0,lN!6kpH$9hrcrN2rrN#kU%4qXfm)k6GlrN!6J%c,`rj!8a!crN!fb2IAk@B,rN!AqXb26rrr!QIq3rrq30+S!DIcrrlF1E2lrrrk5#8Qjrj!*rHfpTlRNqrq3"-B*rrrrll([rj!&pr'c,I2j@(rrN!@p2c2Crrq@5[q3rrq30+S#M[rrrrFI(qVrrr3q-V9jrj!)rUXiF*5!3hVYrrrrb!MrN!5SBH$rrrriBAkd+I,j@(lrN!Afj2Mrrrq10[q3rrq30+S$N[q3"$F6b[rraJ0qm@$arj!(U5r'rIrqmeY9mIrrb`MrN!6pTMR3rZG950ke+2,j9hlrrrrqelM8m[hrrimdrj!%r[Rmrj$rrj!YUJ15rj!%14,&rrYT"p6rQDArN!Eq1RRqrj!%bbDjrrr1"rq3"IQ5-,CdNH[rYL6Ij9"prrrr[NNj6PjPD'G22@9H8dBj0Q[qrj$rrj!XUJ+2rrrrq53AeIrE*8,frq09p2q3"IS@SIq3"H)QS[rrc`IrN!EjA#r$rrrrYa"SDbCprrrrl0l0iHlcp*!%mqRA`DUZdIq3rrq3,DS!B2[rrli1-[MrP3@8r[rl5-hrN!BhE[q3"F3N[Irrc`ErN!IL)C6rrrqi*[,k@AcrN!6qd(KNT[(rN!6pcRjRmrq3rrq3,US"0)klVLS1TIh6,`bjqrlVAeRKrj!&XbQJr2rqhdKRp[rrc`ErN!KL-[hrrlNQm[TCI2q3"[V6DM#1jHHP4La'VrcrN2rrN#kU!ih"F$j)U[IeJ'0MJH[kUfjRQ[q3"IUf8@CeF9D4lIrrrmi&rj!%qVjaU$Y*Y,MeZLAbqPPlrj!)pVN`,9HC`pR`rj$rrj!`UJ15rrrprj!9q-iVFqrrN!A*"Iq3"1Z3!)b@NA**@HDP'r$k@AVrN!Ejp2IkebSXl2clqrlrN2rrN#qU!j,rN"RiZHrrN!DU![MrN!Z0+9lfmNPVrIq3"0G&'6eHEMBKB@0JAEhrN2rrN#qH!j,rN#'R1NVerj!,lZ[hkQBcS2hrN!6bi1MTN!6Pbk'&K0IrN2rrN#kU44LBrj!KiGVcrj!2ppMLrIq3rrq332cPbq(rN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN2rrN*MhdE+MS+rBqrq3rrq3FH+3!$`D#`-"#4jNf[q3rrq3E[Uh,3-!N!F"-H6rN2rrN'cjL`S!N!YAp2q3rrq3D[f'#J!!!bNf"J#3"JE!rj$rrj"TrVF6!!!+C0cSN4-!N!CVr[q3rrq3D2!Y!!!-QrArrrb*!`#3"6MZrj$rrj"RqRF!!"kmrj!&ldN!N!8Ie2q3rrq3Cm)6!#Hrr[q3"V!!N!82a2q3rrq3C[01!#(!r[q3"qX!N!8'Zrq3rrq3CUF+)XVqrj!)l`#3"3'frj$rrj"Pm8G`jrq3#Zm!N!8"Y[q3rrq3CIRNqIq3#qm!N!8#Yrq3rrq3Fqm!N!8&Z[q3ir(*TBYrIBLNbrIrN)A[!*!&#VrrN0rjcBj&%3F%!J%!!33)'@+mp[q3G[A2XCjY-aB9-RE-qqm!N!84a[q3#I$+cH,krj"!p0IFl2hrN!r0SE[rN&hedTYN3c53#68k5@LKhrq3#E%C!`#3$"&8b2lrN%chd1$frj!Ll*Jp'JN"!*!''''h!*!&'FrrN!MC3KFC*%#Kr2q3%2crlDpC3E$lrj!1rE9'0%23rj!2m-Z"0"iK+MeYU0Ihrj!,I3%8f2q3'Ih!lrq3'IH9h2Iqrj!JrFjD&J#3%!%hfIq3#+%!N"!DSrRrN%[Y15P9V2IrN"lqf%8$!*!-$`#3"56Drj!(pdN"!*!%&plrN"#CJ$i(!!!Berq3$ZJh!!!)Vrq3$2VIN!"$%3#3"`)E@,Rdrj!*JJ!'`rq3'FCCpIq3'PJ+3(k[f[crN"cjPJX!N"-#S2q3#+%!N"%'L[MrN%ZB"3!!60VrN"h2*`#3&$,Rrj!(X!#3"KMVrj!3FJ#3"ScrN!l@(J!!!*6rN!VpaPS0!*!0!d#irj!)J3!(hIq3'28k@2q3'p3K!!%)%#0DNVhJrIq3&[Cq"`#3&CRrN!LK!!%B6iQkfZAHa)p-%3#3"3U-rIq35ZBA!!!"-pArN"[T1`#3&86irj!'p93!N!C4r[q3%*8!N!CGrj!1e"X!!!##rj!*h'`0!3#3%!Yhl[q3"RX!#1[rN"IlL!&`rj!ErQN!N!B"$LK0J,(Dl[hrN"$pNJ`!N!F+)NGhRE5e8!#3"jcrN!LP+),5p[q3"r2"433!N!39YIq35d)!!!!"8IIrN"U""3#3&@6rN!I5&`#3"3LTrj!4V`#3"NrrN!l$#J!!!(IrN!IlX$%#!*!'$$%M!3#3#34Kl2q3"A%!"XrrN"I)'J#%rj!FX`)!N!S"%d"i`rVqrj!0b4F!N!B2AUcNr[q3"0F2!*!&!ClrN!MMiIq3$2"K"!#3"#Mbrj"+H!#3"!Zarj!Ck48!N"D5rj!(K3#3"LRJrj!4a!#3"NRrN!k3!!#3"(crN!EiN3`!N!B$3Dhad$)"!*!*"(Mqrj!%C3!%UIq3&[*0!!#@rj!Ff4i!!53*!*!+!5H(hIq3#rBf!*!'*F[rN!Ma33#3"35Prj!Ap&i!N!9qqrq35D!!N!91qrq3&rf$!3#3&32-rj!'k5i!N!C+rIq3%G%,!*!&4rq3$ISp!*!%K[q3"I&`!3#3"L#Uq[rrrq44!*!+%-ArN!4A!!&pr[q3&BN&!!#Srj!FkcX!!#D8-`-!N!S$(RcRrj!)rCJ#!*!%!cM3r[q3#2PH!*!&#V$rN"ME+J#3""[Crj!Rj2crN##i#3#3"!hZrj!Akbm!N!F',dBr%3#3#LVTrj!'TJN!N!CYrj!5fK`!N!9&rj!0a"-!N!53!2q3"2CZ"J#3"301eIlrN!AVEJF!N!J"E2hrrrp*!!"@prq3&0)@!!!!Z2q3(2K3!!!$C1+#(`)!N!S"2-,mrj!'j$%!!!!(,SVLrj!+r@d!N!86`rq3'2f6!*!&KIlrN#DCp[q3)-)4!*!&arq3&lX$!*!'%CMNq[5k03%!N!KPq[q3"Ie+!*!(NIq3%Z3Z!*!&3[[rN!aS!3!!!!+JrrrrrT!!#3#3"3*EjIq3#2D%%!#3##hkrrrr23!!,ZhrN"2d9!%!!!$'rj!G@J!!!!E"rpKV"J#3#aQZrj!'S!%!!"+4mrq3$2jb!*!&(YVrN"RZ&`#3"$6Vrj!Pp%IXrj!Jb"8!N!@Zrj!AE!#3"JQ9rj!&ebd!N!F#V2q3"YJ0!*!(Y[q3%["%!*!&12$rN![X$`#3"!UcrrrreJd!N!8"4ZrrN!VmP3X!N!F,q2rrrc%!!!A5rj!6V3-!N!6Arj!G@J#3"%(`rrl6AJd!N!S4Z[q3"23q!!!-U2lrN!hjA3#3"66jrj!Cr@`!N!3-ZIq3*EBIhrq3)-`C!*!&ZIq3&ZNe!*!'3IMrN!E!#`#3"Jlcrj!'M`-!N!B%e[q3%[jN!*!&)GErN!VqL3%!N!3@b2rrmNi!N!BMirq3$2bF"!#3"J,irrrr+!!!!(hrN",P-`#3"!MNrj!G@J#3"!@crrrrpF*4#J#3#5hYrrrrb4F!!%rcrj!1eaX!N!9Rrj!EV3N!N!4qrj!NrAJ&eIq3)-mE!*!%$16rN"E+&!#3"3+Drj!(q'3"!*!&6rq3"[PE!*!(%plrN"1#!*!&"UMrN!VV03#3"5,Grrqq#3#3"3HArj!1pfN$!*!&"rMrrrmP!!!!-q6rN"'9"!#3""lUrj!G@J#3"96irj!%pTSJ!3#3#*Iqrrqa"J!(Z[q3$Z98!*!&!UhrN!rmmqcSjqMZprq3"0m@!*!%3Iq3*2""!p6rN#$3(!!!!!*YrIq3&U8#!*!&)p[rN!M2#`#3"!5Arj!'mcX!N!FSj[q3%jm!N!C0qrq3#EB%!*!&0rMrrQF!N!BZj[q3$q)H!*!&%rRrrrmU!!!!"U2rN"$[0!#3"6Varj!G@J#3"4c5rj!'e8F!N!K%m2rrX!8#G[IrN!h+2J%!N!8QhIq3$ILlFciG#3)-*P5Gm[rrrL`!N!3Dmrq3)pi2#YIrN#$4(3!!!"cMrj!AF!#3"QAlrj!*53#3""M2rj!'m#F!N!G'mIq3%ld!N!B,XIq3#2TA!*!'C2rrk#m!N!CZrj!4FJ#3"56jrrrr1!#3"$[hrj!2V`X!N!9HqIq3(@%!N!8"S2q3"r"*!3#3"KRDrrq`(j2krj!,p,pR#J%!N!CbrIq3#rZX0!F"!*!("#HMq2pA!*!%%G(rN#1P!"2Erj!JdKd!!!"1rj!B23#3"3,%rj!+S!B!!!!`prq3"[!U!*!(F[hrN"2D!*!((pVrN!I1'J#3"TcrrmN@!*!'U[q3%D-!N!8rqrrrrdm!N!3,V[q3$e8!N!8#N!$rN"jb!*!'DIq3#0FE!*!'"-rrrpc+r2q3#IVFQ$i5!*!)$Y(rN![VG3d!N!`1GI9i!*!%#lIrN#,pB`!Hi2q3)0-H!!!!0pler2q3&1mJ!*!&1I2rN!VD)!!!!'(rN!Id2J#3"llrN"6`"3#3"d,Drj!'J!%!N!84c[rrY`J!N!E'rj!4R3#3"@(prrrrE`#3"8Vprj!0jJi!N!8)c[q3(S)!N!C"rj!*C`#3"mRrN![ppEpP)`#3#J*Yq[q3#[&M!`#3$J1"M!#3"!DMrj!LkM3!+qArN#$8(`!!!!)Q5eKGN!9HC(53!-$Zqrq3#0!9!*!%"k$qrj!+r83!!!#Drj!(qQ%!N!B8q[q3&28C!*!)4YlrN!64(J#3"MlYrrq[!3#3"XMrN"&d!*!%!BMrN!59!3#3"!66rj!-rBX"!*!&,2[rN"k4!*!'+rq3#D8"!*!'cIq3#H#RF5d"!*!-,ZMrN!Y`"!#3"KY4F(KS33N!!!!&83#3"!18rj!LaK%!+Ufm[X$%bpcfrj!Ce5!!N"%9CYRrN!H`#`#3"%hkrj!-IJ!!%XhrN!L8!`#3"8ErN"Ah-3#3#6rerrl2+`#3"hcrrrqa!`#3"V6rN"$e+J#3"!bhrj!%[3m!N!9PqIq3#q8P!*!&"TArN"qI!*!')rq3#EX+!*!&"p(rN!ITH4-(!*!1*F6rN!Zk#`#3"4Q4j[Ipr[[cdeX*!!!%!*!%!BhrN"hPPe0$G'`"!!-+#``-$3i5'MpmaIErN"AA)3#3%J%ESIArN!@5!J!!!$ICrj!0Y3)!21crN!M5#`#3"8(rN"Aj4`#3#30AM9S8!*!("p2rrrql#`#3"S,rN!rpPJF!N!3HkIq3"13T!*!&$m6rN!VkHJ%!N!8kl2q3(kS!N!BMrj!*`a%!N!85e[q3"Ibr333!N!i",llqrj!+mdJ!N!8NZrlrN!IcK3N!N!H*rj!Dqq'F-!3!!!!$!*!+!3SC3Dcmrj!8f#)!N"3-E1hrrrrqE3!!!#R(rj!1d4!!F[lrN!Ml*J#3"3c4rIq3%rYD!*!%'4X!N!i"6IMrrrr1'J#3"Mrbrj!0rFXD!*!&9rq3"IeE!*!'5HVrN!Qh&`#3"3ZXrj!JY3#3"L2rN!Qp$3#3"5(Hrj!%rC`9!*!1!3YLhIq3$-S&!*!%$+RrN!VeBJ#3"J',rj!BqmpY*J%!N!`#!aC-JUl6q2q3&YSN!*!%"*!'!`)"!*!)"((rrrrp43!!&-Iqrj!1h#-!`2rrrrllN!CL!*!'*Bh4mI[lr2hqrj!-r'X!N!4ET3N!N!d0[[q3"1Sa!*!'#k6rN!cq`LJ!N!8(V2q3"Ui#!*!&"@llrj!(e#N!N!CVp[q3),m!N!BMrj!*L3#3"METrrrrqT)"!*!0#d+)h[q3$R-!N!9LqIq3#qS9!*!&!T(rN"EVded&!*!)!`!!!"j(FkIEr2q3'p`Q!!!!%XhrN!6filb"1JF!N!F,errrr"F!(-2rN"$T1#[`rrrr``m!N"!#$#*$FD,9r[q3#Ijk!*!%GIbJ"`#3#`4irj!'D!#3"a+br2q3#HGc$3#3"MhYrj!'k6F!N!B%@q2rN!6iVKJ!N!BkmIq3)FF!N!BMrj!)rN8!N!C1pIrrrlN3!*!*##*!F+MCm2lrN!Mqrj!&m%!!N!3%`rq3$2eV!3#3"!@Erj!@q[ESeV5PUV5qap(DR3!!"F(brIq3(YdQ!!!!!@Vprj!'rZke43)!N!8$N[rriJ%GYIlrN"$a4R6mrrrrm9!!N"8(&N+Bf[hrN!H$!*!%LrrlN!!3!*!*"',Yrj!'`JS!N!F1ClcJp2[jmGZmG#)$!*!'#+hrN!IqR!#3"`)PEk5XL%!-!*!'-0MrN#,1!*!')rq3#0iA!*!'ErlrrrP0!*!'!K-mK,MApIq3$1$'rj!&fb3!N!3Pl[q3$Dd*!*!%#+VrN#+e!!!3fIq3)0iR!*!%%ZVrN!RZG!X!N!9Pq[q[&DVmrj!4p9E(rj!&cc!#!*!,"!#3#J-PF0Vkrj!&K3#3"+(rrrQK)`%!N!8"%AVYrj!(meN!N!N0+N"'4$`Q#`#3#9rdrj!)mM8!N")",mRrN#29!*!'*Iq3"rk4"!#3"U$rrrrB)J#3"3YXc2hrN!rd@CRrN!A-%J#3"&,hrj!0f"3!N!3-Zrq3)V8!!#(Krj!Jh5B!N!@Mrj!+qhN#!*!%426rVF$prj!5qBVprj!'jSTSA%mM!3#3"S4V,J-!N!S9GZ6rrrrqJ!#3",MrN!6CEaS!!!)RE-ErN!VI(3#3'#rVrj!+[Jm!N"%qe[q3*0X!N!BTrj!(pM-!N!B#h2rrrlX0!*!%(FIprj!4N`D(rj!&`JB!N!4Ur2q3$HmD!*!%%YIrN#+e!!"%m2q3)0SN!*!&N!$rN![Y4!#3"#[[rrlrN"6pl2q3#Ihpr29`!*!'erhlqC!-q[lrrrrqH`#3"-rrN!Apq16GlrVprj!-e8J'!*!8!NVJrj!,rTB-!*!1#'6crj!Ph`#3"M$rN!EqV!-!N!BPprrrrk)"!!!!$UlrN",Q)J"Srj!&[`%!N!4er[q3$ISF!*!%'r,rN#+e!!"Zr2q3)03I!*!&Trq3$*S!N!3El2q3*F3!N!EArj!6rA8!!!!,h2q3'HfV64d&!*!2!b5'k2q3$IH2%3#3#`-aS[ArN#EN!*!'22q3"ZNr!*!(Crcrrrq'!*!%22VrN"(mI`-!52q3"F!%!*!%FIhrN!he'`#3"$[rN#1e!!#jrj!Kc"N!N!A0rj!-dJ#3"!rTrj!Pc!#3"YIrN"2mC`!!!#$Nrj!EqY'UH8mZ'4H3#"mcACVErIq3$rUc+3B!N!F((SAJrj!Sj`#3"NhrN!AqL3)!N!B*V2q3"(!!N!4Xrj!5fK-!!$2rN!A($!#3"',krj!0jaJ!N!4`rj!MY3!Gprq3)F35!*!%$I2rN!cI!*!%"qMrN#A-!*!'erq3%rYA!!!!11crN%(`ReBN#J34-QDQlIq3+ZN!N!CRrj!&ZaF!N!FNl[q3"'-!N!4Jrj!4p&`!!!"*rj!&e4i!N!3mm[q3$F)1!!!!"UlrN#1e")Vqrj!KZ!J!N!4%qrq3$-3!N!3#jrq3*F`!N!EArj!6q8F!!!"9prq33rRcm1rapI[rN#cV!*!'KIq3"0XZ!*!("B[rN!9J!*!%+ZrrN!rfL`S!!!1)rj!&kMF!N!34iIq3$2k4"!!!!#6Crj!MY5MMrj!LU3%!!!!#K[lrN![qJJ#3"!,Rrj!Pc3%!N!3%fIq3%rF[!!!!HIlrN(EX!*!&!UhrrrrQ23%!N!Fjk2q3"AB!N!3(Q2q3$IlaF3X!!!!Jf2q3"IaL!*!&PIlrN![i2J#3"&Rlrj!Mb+MrN#13!!#3"!r#rj!-h#X!N!3-kIq3*G%*!*!%%prrN"2d&3!!!DVrN(IY!*!&'Flrrmif!*!)%EhrN!Di$3#3""29rj!,p+3X!*!%"jArN!Hf!*!&,H$rN!ZZ!3!!!!@jrj"*E!#3"#Ihrj!,hNF!N!8MlIq3*Hk-H*!%N!$crj!6k3%!!!,Rrj"hk`#3"8,aqD-L!3#3"`+9qrq3"[%p!*!&00,rN!Imfj3c#!#3"!0bp2q3"qie!*!%!Q$brj!*c5N!N!4*m2q358N!N!3mVT!*VCe`'`)!N!9*pIq33-)!!!!`r[q3GqB!N!3$NY9L#`#3#!CPqIq3#)8!N!BdZ2,mq1hGUPiP!J#3"3GXm2q3#2kM"`#3"!GKjIhrN!Aj[M8!N!3([rq35IiT!*!BE2crN%#B!!!"H2q3H0d!N!3QAaX!N!N$DI2rN!R#!`#3"JY*BeJp&3%!N!F(G2MrN!Vk8!#3"Lb%b[$jjVCN%!#3"!0Rrj"+laF!N"F%Q[q33@d!!!kkrj"icJ#3$`q-p[q3#ZBZ!*!6$jAmrj!-jN)!N"%"6[(rN%V5%!#3&bIYrj"!q&)!!$,erj"iZJ#3$33aZ[VrN![lK!#3%K#Mq[q3$YT1!J#3$J09i2q35lJ,!*!9#NA(rj""l6m!!SRrN(QK!*!+""-pPq,rN!l`4!)!N!m@R[hrN"$UG48#!*!+!4*kkrq36+)'!*!("3d8("q3"L3a5hHhl2q33Z)T!#RDrj"jK!#3##4EPG$mrj!4j9%#!*!0-VMrN"6-EK`!N!J@D-RrN%kH"3!!!!JeAS+IZpIcrj"1e"!#Q[q3HIjJ!!!"%d&[U1$jr2q3&IH[9#S6"`)%#"!I-Nef[rArN"EppmUDHfTTGj6$pIhrN%qH"4"5V1Vkr2lrN&+k!h(hrj"jq@BU9k2Al[hrN"[fj0R5d0(6eplRp2lrN(1P@-Aerj"AS'lbrj"lj16prj#Hjr2rN&RQq2q3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3rrq3M300"""

    import binascii
    _ds9_python_logo = binascii.a2b_hqx(_ds9_python_logo_text.encode("ascii"))[0]
    return binascii.rledecode_hqx(_ds9_python_logo)


_ds9_python_logo = _load_logo()


def test():
    _ds9 = ds9()
    import time
    time.sleep(1)
    d = numpy.reshape(numpy.arange(100), (10,10))
    _ds9.view(d)
    time.sleep(1)
    del _ds9


if __name__ == "__main__":
    test()

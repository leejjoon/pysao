

#x = [1,2,3]
#y = [2,1,3]

def region_group_delete(ds9, group):
    ds9.set('regions group "%s" delete' % group)


template_point_sky="fk5;point(%e,%e) # point=circle tag={%s}"
    
def to_ds9_region_points(x, y, group="ds9", region_template=None):
    _r = ["""# Region file format: DS9 version 3.0
# Filename: stdin
global color=green font="helvetica 10 normal" select=0 edit=0 move=0 delete=1 include=1 fixed=0 source"""]

    if region_template is None:
        region_template = "image;point(%e,%e) # point=circle tag={%s}"
    region_strings = [region_template % (x1,y1,group) for x1, y1 in zip(x, y)]

    return "\n".join(_r + region_strings + ["\n"])

def to_ds9_region_circles(x, y, r, group="ds9", color="green"):
    _r = ["""# Region file format: DS9 version 3.0
# Filename: stdin
global color=%s font="helvetica 10 normal" select=0 edit=0 move=0 delete=1 include=1 fixed=0 source""" % (color)]

    try:
        _l = len(r)
    except TypeError:
        r = [r] * len(x)
        
    region_template = "image;circle(%e,%e,%e)" + " # tag={%s}" % (group)
    region_strings = [region_template % xyr for xyr in zip(x, y, r)]

    return "\n".join(_r + region_strings + [""])

from ann import kd_tree
import numarray as NA

def function_print_aux(x, y, aux):
    a = NA.array([x,y])
    a.transpose()
    tr = kd_tree(a)

    def print_auxdata(x1, y1, f1, c, tr=tr, aux=aux):
        if c == 'a':
            _i, _d = tr.search1(NA.array([x1, y1]), 0.)
            print aux[_i]
            return x[_i], y[_i]
        
    return print_auxdata


        
def examine(f):
    s = ds9.readcursor().split()
    while s[3] != 'q':
        f(float(s[0]), float(s[1]), int(s[2]), s[3])
        s = ds9.readcursor().split()

def xy_examine(x, y, aux):
    _f = function_print_aux(x, y, aux)

    def _f2(x1, y1, f1, c, _f=_f):
        x1, y1 = _f(x1, y1, f1, c)
        grp_name = "__xy_examine_f2__"
        region_group_delete(ds9, grp_name)
        region = to_ds9_region_circles([x1], [y1], 5,
                                       group=grp_name, color="red")
        ds9.set("regions", region)

    grp_name = "__xy_examine__"
    region = to_ds9_region_points(x, y, group=grp_name)
    ds9.set("regions", region)

    examine(_f2)

    region_group_delete(ds9, grp_name)


from cube import make_mask_from_region

def get_flux(d):
    region = ds9.get("regions -format ciao -system image")
    m = make_mask_from_region(d, region)

    dd = d[m]

    print 
    print " ********************************* "
    print "sum         -> ", dd.sum()
    print "area(pixel) -> ", len(dd)
    print "Mean        -> ", dd.mean()
    print "Std. dev    -> ", dd.stddev()

    return dd.sum(), len(dd), dd.mean(), dd.stddev()


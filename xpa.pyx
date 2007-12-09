
cdef extern from "stdio.h":
    pass

cdef extern from "stdlib.h":
    void free(void *)

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, int len)
    object PyString_FromString(char *s)
    int PyString_Size(object s)


cdef extern from "xpa.h":

    ctypedef struct XPARec

    XPARec *XPAOpen(char *mode)

    void XPAClose(XPARec *xpa)


    int XPANSLookup(XPARec *xpa,
                    char *template, char *type,
                    char ***classes, char ***names,
                    char ***methods, char ***infos)


    int XPAGet(XPARec *xpa,
               char *template, char *paramlist, char *mode,
               char **bufs, int *lens, char **names, char **messages,
               int n)

    int XPASet(XPARec *xpa,
               char *template, char *paramlist, char *mode,
               char *buf, int len, char **names, char **messages,
               int n)

def nslookup(template="*"):
    cdef char **classes
    cdef char **names
    cdef char **methods
    cdef char **infos
    cdef int i, n
    cdef int iter
    
    #first run
    n = XPANSLookup(NULL, template, "g", &classes, &names, &methods, &infos)

    l = []
        
    for i from 0 <= i < n:
        #print "%s %s %s %s" % (classes[i], names[i], methods[i], infos[i])
        s = PyString_FromString(methods[i])
        l.append(s)
        free(classes[i])
        free(names[i])
        free(methods[i])
        free(infos[i])
            
    if n > 0:
        free(classes)
        free(names)
        free(methods)
        free(infos)


    return l


#class _pyXPA:
#    XPARec *xpa
#    def __init__(self):
#        self.xpa = NULL

cdef _get(XPARec *xpa, char *template, char *param):
    cdef int  i, got
    cdef int  lens[1]
    cdef char *bufs[1]
    cdef char *names[1]
    cdef char *messages[1]
    
    got = XPAGet(NULL, template, param, NULL, bufs, lens, names, messages, 1);

    if got == 1 and messages[0] == NULL:
        buf = PyString_FromStringAndSize( bufs[0], lens[0] )
        #print buf
        free(bufs[0])
        free(names[0]);
    else:
        if messages[0] != NULL:
            mesg = PyString_FromString( messages[0] )
            free(messages[0]);
        else:
            mesg = "XPA$ERROR   XPAGet returned 0!"

        if ( names[0] ):
            free(names[0])
        if( bufs[0] ):
            free(bufs[0])
 
        raise mesg

    return buf
    
def get(template="*", param=""):
    return _get(NULL, template, param)


cdef _set(XPARec *xpa, char *template, char *param, buf):
    cdef int  got
    cdef int  length
    #cdef char *bufs[1]
    cdef char *names[1]
    cdef char *messages[1]

    if buf:
        length = PyString_Size(buf)
    else:
        buf = ""
        length = 0
        
    got = XPASet(xpa, template, param, NULL, buf, length, names, messages, 1);

    if got == 1 and messages[0] == NULL:
        #buf = PyString_FromStringAndSize( bufs[0], lens[0] )
        ##print buf
        #free(bufs[0])
        free(names[0]);
    else:
        if messages[0] != NULL:
            mesg = PyString_FromString( messages[0] )
            free(messages[0]);
        else:
            mesg = "XPA$ERROR   XPAGet returned 0!"

        if ( names[0] ):
            free(names[0])
 
        raise mesg

def set(template="*", param="", buf=None):
    _set(NULL, template, param, buf)

cdef class xpa:
    cdef XPARec *_xpa
    cdef char *_template
    
    def __init__(self, template):
        self._template = template
        self._xpa = XPAOpen("")

    def __del__(self):
        XPAClose(self._xpa)
        
    def get(self, param=""):
        return _get(self._xpa, self._template, param)


    def set(self, param="", buf=None):
        _set(self._xpa, self._template, param, buf)



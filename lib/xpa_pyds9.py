import xpa as _xpa

class xpa(object):
    
    def __init__(self, template):
        self._template = template

    def __del__(self):
        pass
        
    def get(self, param=""):
        return _xpa.xpaget(self._template, plist=param, n=1)[0]


    def set(self, param="", buf=None):
        return _xpa.xpaset(self._template, plist=param, n=1)

class XpaException(Exception):
    pass



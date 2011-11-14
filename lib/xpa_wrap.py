from pysao.xpa import XpaException, xpa

class XPA(xpa):
    def __init__(self, template):
        xpa.__init__(self, template.encode("ascii"))

    def get(self, param=""):
        return xpa.get(self, param.encode("ascii"))


    def set(self, param="", buf=None):
        xpa.set(self, param.encode("ascii"), buf)



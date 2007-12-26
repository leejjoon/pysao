
import StringIO

import formatter


import re
p_sy = re.compile("Syntax:\s*")
p_ex = re.compile("Example:\s*")

#_trail_comment = r"(\s*(#.*)?)"
_trail_comment = r"(\s?)"
_redirect_file = r"\s*>\s*([\w.]+)"

#p_xpaget = re.compile(r"\$xpaget\s+ds9\s+([\s\w\d\-\+:.{}'\"]*)")
p_xpaget = re.compile(r"\$xpaget\s+ds9\s+(.*)")

p_xpaget_wo_ds9 = re.compile(r"\$xpaget\s+([\s\w\d\-\+:.{}]*)")

p_xpaget_w_redirect = re.compile(r"\$xpaget\s+ds9\s+([\s\w\d\-\+:.{}]*)" \
                                 + _redirect_file)

p_xpaget_mask = re.compile(r"\$xpaget\s+mask\s*([\w\d\-\+:.{}]*)")

#p_xpaset = re.compile(r"\$xpaset\s+-p\s+ds9\s+([\s\w\d\-\+:.{}'\"]*)")
p_xpaset = re.compile(r"\$xpaset\s+-p\s+ds9\s+(.*)")

p_xpaset_wo_ds9 = re.compile(r"\$xpaset\s+([\s\w\d\-\+:.{}]*)(\s*(#.*)?)")

p_xpaset_w_echo = re.compile(r"\$echo\s+(.+)\s+\|\s+xpaset\s+ds9\s+(.*)")

p_xpaset_w_cat = re.compile(r"\$cat\s+(.+)\s+\|\s+xpaset\s+ds9\s+(.*)")


from tokenize import generate_tokens, COMMENT

# comments are detected using tokenize.generate_tokens
def takeout_comment(s):
    
    g = generate_tokens(StringIO.StringIO(s).readline)
    c = [tokval for toknum, tokval, _, _, _  in g if toknum == COMMENT]
    if c:
        return s.replace(c[0],"").strip(), c[0]
    else:
        return s, ""

def _convert_syntax(l):

    l, c = takeout_comment(l)
    # SET
    if p_xpaset_w_echo.search(l):
        #print l
        r = p_xpaset_w_echo.subn(r"ds9.set('\2', \1)", l)[0]
    elif p_xpaset_w_cat.search(l):
        s = r"r=open('\1').read(); ds9.set('\2', r)"
        r = p_xpaset_w_cat.subn(s, l)[0]
    elif p_xpaset.search(l):
        r = p_xpaset.subn(r"ds9.set('\1')", l)[0]
    elif p_xpaset_wo_ds9.search(l):
        r = p_xpaset_wo_ds9.subn(r"ds9.set('\1')", l)[0]

    # GET
    elif p_xpaget_w_redirect.search(l):
        s = r"r = ds9.get('\1'); open('\2','w').write(r)"
        r = p_xpaget_w_redirect.subn(s, l)[0]
    elif p_xpaget_mask.search(l):
        r = p_xpaget_mask.subn(r"r = ds9.get('mask \1')", l)[0]
    elif p_xpaget.search(l):
        r = p_xpaget.subn(r"r = ds9.get('\1')", l)[0]
    else:
        if l:
            if not l[0] == "#":
                print "WARNING : failed to convert (%s)" % l
        r = l

    if c:
        r = r + " " + c

    return r


import htmllib

class parser(htmllib.HTMLParser):
    def __init__(self):

        self.nullwriter = formatter.NullWriter()
        self.fmtr = formatter.AbstractFormatter(self.nullwriter)
        htmllib.HTMLParser.__init__(self, self.fmtr)

        self.help_strings = dict()

        self.fmtr.writer = self.nullwriter
        
        self._current_help = ""
        self.h4 = False
        
    def start_h4(self, attrs):
        self.h4 = True
        self.h4_title = ""
        
    def end_h4(self):
        #print self.h4_title

        if self.h4_title:
            f = StringIO.StringIO("")
            self.help_strings[self.h4_title] = f
            self.fmtr.writer = formatter.DumbWriter(f, 800)
            
        self.h4 = False


    def handle_data(self, d):
        if self.h4:
            self.h4_title = self.h4_title + d.strip()
        else:
            htmllib.HTMLParser.handle_data(self, d)

    def get_help(self):
        r = dict()
        
        for k, v in self.help_strings.items():
            s = v.getvalue()
            v.close()

            ## Syntax : 
            ss = p_sy.split(s)
            if len(ss) != 2:
                print k
                r[k] = s
            else:
                expl, _rest = ss
                # replace "nbsp"
                expl = expl.replace("\240", " ")
                
                ## Example : 
                syntax, example = p_ex.split(_rest)

                # replace "nbsp"
                syntax = syntax.replace("\240", " ")


                ex_ = [_convert_syntax(l) for l in example.split("\n")]
                example = "\n".join(ex_)

                r[k] = dict(expl=expl, syntax=syntax, example=example)
                              
            #print h.help_strings["header"].getvalue().replace("\240"," ")
        return r


#open("xpa.html").read()
def parse_xpa_help(s):
    h = parser()

    h.feed(s)
    h.close()
    r = h.get_help()

    return r


from pysao.verbose import verbose

#import StringIO
import formatter

import sys
if sys.version_info[0] >= 3:
    import io as StringIO
else:
    import StringIO


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

# We use "xpa[sg]et" due to the bug in the xpa.html
p_xpaset_w_cat = re.compile(r"\$cat\s+(.+)\s+\|\s+xpa[sg]et\s+ds9\s+(.*)")


from tokenize import generate_tokens, COMMENT

# comments are detected using tokenize.generate_tokens
def takeout_comment(s):

    g = generate_tokens(StringIO.StringIO(s).readline)
    c = [tokval for toknum, tokval, _, _, _  in g if toknum == COMMENT]
    if c:
        return s.replace(c[0],"").strip(), c[0]
    else:
        return s, ""


example_typo = {"$xpaget -p ds9 lock frame":"$xpaget ds9 lock frame",
                "$xpaget -p ds9 lock crosshair":"$xpaget ds9 lock crosshair",
                "$xpaget -p ds9 lock crop":"$xpaget ds9 lock crop",
                "$xpaget -p ds9 lock slice":"$xpaget ds9 lock slice",
                "$xpaget -p ds9 lock bin":"$xpaget ds9 lock bin",
                "$xpaget -p ds9 lock scale":"$xpaget ds9 lock scale",
                "$xpaget -p ds9 lock colorbar":"$xpaget ds9 lock colorbar",
                "$xpaget -p ds9 lock smooth":"$xpaget ds9 lock smooth",
                "$xpaget -p ds9 lock color":"$xpaget ds9 lock color",
                }


def _convert_example(l):

    l, c = takeout_comment(l)

    if l.strip() in example_typo:
        l = example_typo[l.strip()]

    # SET
    if p_xpaset_w_echo.search(l):
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
                verbose.report("WARNING : failed to convert (%s)" % l,
                               "helpful")
        r = l

    if c:
        r = r + " " + c

    return r


def _reindent_syntax(syntax, k):
    ll = []
    indent = " " * (len(k)+1)
    for l1 in syntax.split("\n"):
        l1 = l1.lstrip()
        if l1.startswith(k):
            ll.append(l1)
        else:
            ll.append(indent+l1)
    return "\n".join(ll)


import sys

if sys.version_info[0] < 3:
    #import htmllib
    import HTMLParser
    from htmlentitydefs import name2codepoint
else:
    import html.parser as HTMLParser
    from html.entities import name2codepoint


class Parser(HTMLParser.HTMLParser):
    def __init__(self, **kwargs):

        self.nullwriter = formatter.NullWriter()
        self.formatter = formatter.AbstractFormatter(self.nullwriter)
        HTMLParser.HTMLParser.__init__(self,  **kwargs)

        self.help_strings = dict()

        self.formatter.writer = self.nullwriter

        self._current_help = ""
        self.h4 = False

        self.saved_data = ""

    def handle_starttag(self, tag, attrs):
        if tag == "h4":
            self.start_h4(attrs)
        elif tag == "a":
            self.start_a(attrs)
        elif tag == "pre":
            self.start_pre(attrs)
        elif tag == "br":
            self.do_br(attrs)

    def handle_endtag(self, tag):
        if tag == "h4":
            self.end_h4()
        elif tag == "pre":
            self.end_pre()
        elif tag in ["tt"]:
            d = self.flush_data()
            self.formatter.add_literal_data(d)
        elif tag in ["p"]:
            d = self.flush_data()
            self.formatter.add_literal_data(d)
            self.formatter.end_paragraph(0)


    def handle_entityref(self, name):
        if name == "nbsp":
            c = " "
        else:
            c = chr(name2codepoint[name])
        self.saved_data += c

    def handle_data(self, d):
        if self.h4:
            self.h4_title = self.h4_title + d.strip()
        else:
            self.saved_data += d

    # For older version of ds9 (e.g., ds9_v5.6), the xpa.html uses
    # <h4>, but in the later versions (e.g., v6.2), they use <a
    # name="#..">.

    def start_h4(self, attrs):
        self.h4 = True
        self.h4_title = ""


    def flush_data(self):
        d = " ".join([l1.lstrip() for l1 in self.saved_data.split("\n")])
        self.saved_data = ""
        return d

    def do_br(self, attrs):
        d = self.flush_data()
        self.formatter.add_flowing_data(d)
        self.formatter.end_paragraph(0)

    def end_h4(self):

        if self.h4_title:
            f = StringIO.StringIO("")
            self.help_strings[self.h4_title] = f
            self.formatter.writer = formatter.DumbWriter(f, 800)

        self.h4 = False


    def start_a(self, attrs):
        dattrs = dict(attrs)
        if "name" in dattrs:

            h4_title = dattrs["name"]

            f = StringIO.StringIO("")
            self.help_strings[h4_title] = f
            self.formatter.writer = formatter.DumbWriter(f, 800)

    def get_help(self):
        r = dict()

        for k, v in self.help_strings.items():
            s = v.getvalue()
            v.close()

            ## Syntax :
            ss = p_sy.split(s)

            if len(ss) == 1:
                # a special case for "psprint" with only description.
                #print "whats going on?", k, ss
                expl = ss[0].replace("\240", " ")
                syntax = ""
                example = ""

            elif len(ss) == 2:
                expl, _rest = ss

                ## Example :
                syntax, example = p_ex.split(_rest)

                syntax = _reindent_syntax(syntax, k)

                ex_ = [_convert_example(l.strip()) for l
                       in example.split("\n") if l.strip()]
                example = "\n".join(ex_)


            else:
                verbose.report("ignoring %s : failed to parse." % k)
                continue

            # fix expl
            extra_kewords = ["cat", "quit", "pmagnifier"]
            filtered_expl = [l1 for l in expl.split("\n")
                             for l1 in [l.strip()]
                             if l1 and l1 != k and l1 not in extra_kewords]

            #expl
            r[k] = dict(expl=" ".join(filtered_expl), syntax=syntax, example=example)

        return r


def parse_xpa_help(s):
    h = Parser()

    h.feed(s)
    h.close()
    r = h.get_help()

    return r

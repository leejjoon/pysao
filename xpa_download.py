
import urllib2

import re

p = re.compile(r"ftp://sao-ftp.harvard.edu/pub/rd/xpa/(xpa-[\d.]+.tar.gz)")

xpa_url = "http://hea-www.harvard.edu/saord/xpa/"
r = urllib2.urlopen(xpa_url).read()

m = p.search(r)

if m:
    url = m.group()
    outname = m.group(1)
    print "..downloading %s" % url
    r = urllib2.urlopen(url).read()
    open(outname,"w").write(r)

else:
    print "ERROR : Couldn't find relavant url from %s." % (xpa_url)
    

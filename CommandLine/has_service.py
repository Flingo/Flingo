import httplib
import json
from urlparse import urlparse
#from urllib import quote


# pulls down resource from given URL and returns the response body as a string.
def get(url):
    (scheme, netloc, path, pars, query, fragment) = urlparse(url)
    lst = netloc.split(":")
    if len(lst) == 2:
        host, port = lst
    else:
        host, port = lst[0], 80
    
    conn = httplib.HTTPConnection(netloc, port)
    
    # http://foo.com/a/b/c?do=blah&po=fa --> /foo.com/a/b/c?do=blah&po=fa
    long_path = "/" + "/".join(url.split("/")[3:])
    conn.request("GET", long_path )
    
    r = conn.getresponse()
    if r.status != 200:
        raise Exception("discover encountered error. returned status: %s %s"%(
            r.status, r.reason ))
    data = r.read()
    return data

try:
    print get("http://flingo.tv/fling/has_service?service=flingo")
except:
    print "Failed to reach flingo.tv.  Is network connected?"

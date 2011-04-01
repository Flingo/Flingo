# Copyright(c) 2011. Free Stream Media Corp. Released under the terms
# of the GNU General Public License version 2.0.
#
# These test the API separately from any given application.  
#
# @author David Harrison

import gevent.monkey
gevent.monkey.patch_all()

import gevent
import gevent.event
import json
import urllib
import urllib2
from urllib2 import Request, HTTPError
from urllib import quote, unquote, urlencode
import sys
from time import sleep
import types
from xmlrpclib import Fault
import traceback

DOMAIN = "dave.flingo.tv"
FLING_ADDR_BASE = 'http://%s' % DOMAIN

VALUE_ERROR = 8004
failed = False

rfp = open("/dev/random","rb")
def randhex():
    return rfp.read(4).encode("hex")


def backend( path, f, referer = None, post = False, **kwargs ):
    """Call the flingo backend."""
    assert not failed, "'failed' set by another greenlet" 
    url = FLING_ADDR_BASE + "/" + path + "/"
    # If using POST then the call and return bodies contain JSON-RPC.
    if post:
        jsonrpc = {
            "jsonrpc" : "2.0",
            "method" : f,
            "params" : kwargs,
        }
        request = urllib2.Request(url, json.dumps(jsonrpc))
        request.add_header( "Content-Type", "application/json-rpc" )
    else:
        url += f
        if kwargs:
            if isinstance( kwargs, dict ):
                for k in kwargs:
                  if type(kwargs[k]) == unicode:
                    kwargs[k] = kwargs[k].encode("utf-8") 
                kwargs = urlencode( kwargs )
            url += "?" + kwargs
        request = urllib2.Request(url)
    if referer:
      request.add_header( "Referer", referer )
      print "calling: %s referer: %s" % ( url, referer )
    else:
      print "calling: %s" % url
    status = 200
    try:
        js = json.loads(urllib2.urlopen(request).read())
    except HTTPError, e:
        if e.getcode() != 400:
            raise
        js = json.loads(e.read())
        status = 400
         
    if post:
        assert js["jsonrpc"] == "2.0"
        if "result" in js:
            return js["result"]
        assert "error" in js, "Neither 'result' nor 'error'"
    if isinstance(js, dict) and "error" in js:
        # SUBTLETY: AS3 in CS5 does not propagate the status code in
        # HTTPStatusEvents and it appears that the response body of any
        # response with a non-200 status code is discarded.  AS2 
        # is similarly incapble of handling non-200 status codes.
        #assert status == 400
        raise Fault( js["error"]["code"], 
                     js["error"]["message"] )
    return js

def get( path, referer = None, **kwargs ):
    """Same as backend except that it doesn't assume the response is JSON-RPC."""
    assert not failed, "'failed' set by another greenlet" 
    url = FLING_ADDR_BASE + "/" + path 
    if kwargs:
        if isinstance( kwargs, dict ):
            kwargs = urlencode( kwargs )
        url += "?" + kwargs
    request = urllib2.Request(url)
    if referer:
      request.add_header( "Referer", referer )
      print "calling: " + url + "  referer: " + referer
    else:
      print "calling: " + url
    return urllib2.urlopen(request).read()

def api( f, referer = None, post = False, **kwargs ):
    kwargs["content_type"] = "json"
    return backend( "api", f, referer=referer, post=post, **kwargs )

def api2( f, referer = None, post = False, **kwargs ):
    if "app_id" not in kwargs:
        kwargs["app_id"] = "flingo"
    return backend( "api2", f, referer=referer, post=post, **kwargs )

def fling( f, referer = None, post = False, **kwargs ):
    if f[0:5] == "fling":
        update_event.clear()
        r = backend( "fling", f, referer = referer, post = post, **kwargs )
        assert update_event.wait(10)  # if no update in ten seconds then fail
        return r
    else:
        return backend( "fling", f, referer = referer, post = post, **kwargs )

def call( f, kwargs={}, guid = "G", service_name = "flingo", 
          referer = None, ttl=None ):
    """Call service with guid and service_name using JSON-RPC."""
    
    assert not failed, "'failed' set by another greenlet" 
    url = FLING_ADDR_BASE + "/fling/call?guid=%s&service=%s" % ( guid,
        service_name )
    if ttl:
        url += "&ttl=%d" % ttl
    print "calling: %s for %s(%s)" % ( url, f, kwargs )
    jsonrpc = {
        "jsonrpc" : "2.0",
        "method" : f,
        "params" : kwargs,
    }
    request = urllib2.Request(url, json.dumps(jsonrpc))
    if referer:
        request.add_header( "Referer", referer )
    request.add_header( "Content-Type", "application/json-rpc" )
    js = json.loads(urllib2.urlopen(request).read())
    if "result" in js:
        return js["result"]
    elif "error" in js:
        raise Fault( js["error"]["code"], js["error"]["message"] )
    assert False, "response should have either 'error' or 'result' fields"
    
def longpoll( guid, referer = None ):
    assert not failed, "'failed' set by another greenlet" 
    url = FLING_ADDR_BASE + "/fling/longpoll?guid=%s" % guid
    print "longpoll: url=", url 
    request = urllib2.Request(url)
    if referer:
      request.add_header( "Referer", referer )
    response = urllib2.urlopen(request)
    assert response.getcode() == 200
    body = response.read()
    print "longpoll response=", body
    msgid = response.headers.get("X-Message-Id", u"")
    service = response.headers.get("X-Service", u"")
    if body:
        result = json.loads(body)
    else:
        result = None
    return result, msgid, service
                    
def set_result( message_id, service, result, guid, referer = None ):
    assert not failed, "'failed' set by another greenlet" 
    url = ( FLING_ADDR_BASE + 
        "/fling/set_result?guid=%s&message_id=%s&service=%s" % (
        guid, message_id, service ))
    request = urllib2.Request(url)
    if referer:
      request.add_header( "Referer", referer )
    request = urllib2.Request(url, json.dumps(result))
    request.add_header( "Content-Type", "application/json-rpc" )
    response = urllib2.urlopen(request)
    assert response.getcode() == 200
    assert int(response.headers["Content-Length"]) == 0

def form_post( path, referer = None, **kwargs ):
    url = ( FLING_ADDR_BASE + "/" + path )
    print "posting: %s" % url
    kw = urlencode(kwargs)
    print "  body: %s" % kw
    request = urllib2.Request(url, kw)
    if referer:
      request.add_header( "Referer", referer )
    response = urllib2.urlopen(request)
    assert response.getcode() == 200
    return response.read()

class RPCServer:
    def echo( self, **kw ):
        #print "echo", kw
        return kw

    def echox( self, **kw ) :
        return kw["x"]

    def update( self, **kw ):
        print "update!!!!!!!!!!!!!!"
        update_event.set()
        return True

    def ping( self, **kw ):
        return True

    def done( self, **kw ):
        return True

    def raise_exception( self, **kw ):
        raise Exception( "hi there" );

    def raise_fault( self, **kw ):
        raise Fault( 9999, "hi there" )

    def return_fault( self, **kw ):
        return Fault( 9999, "hi there" )

    def return_nothing( self, **kw ):
        pass

    def wait( self, **kw ):
        sleep( kw["secs"] )

def handler(guid):
    global rpc, failed
    try:
        
        while True:
           msg, msgid, service = longpoll( guid )
           if not msg:
               continue
        
           #print "handler: longpoll received msg '%s' with msgid '%s'" % ( msg, 
           #    msgid )
           kw = msg.get("params")
           method = msg.get("method")
           id = msg.get("id")
           #print "handler: calling method=%s" % method
           if method and isinstance(getattr(rpc, method, None), 
                                    types.MethodType):
               try:
                   if isinstance(kw, dict):
                       res = getattr(rpc,method)(**kw)
                   else:
                       res = getattr(rpc,method)()
        
               except Exception,e:
                   res = e
        
               #print "handler: res=%s" % res
               #print "handler: res is Fault?",  isinstance(res, Fault)
               if isinstance(res, Fault):
                   result = {
                       "jsonrpc" : "2.0",
                       "error" : {
                           "name" : "JSONRPCError",
                           "code" : res.faultCode,
                           "message" : res.faultString,
                       }
                   }
        
               elif isinstance(res,Exception):              
                   result = {
                       "jsonrpc" : "2.0",
                       "error" : {
                           "name" : "JSONRPCError",
                           "code" : 500,
                           "message" : res[0],
                       }
                   }
        
               else:
                   result = { 
                       "jsonrpc" : "2.0", 
                       "result" : res,
                       "id" : id
                   }
        
               #print "calling set_result msgid=%s result=%s" % ( msgid, 
               #    result )
               set_result(msgid, service, result, guid )
                   
           # calling done() causes the handler to stop handling requests.
           if method == "done":  
               return True
    except:
        traceback.print_exc()
        failed = True
        
def clean():
    assert fling("clear")
    clear_queues()

def clear_queues():
    assert isinstance( fling( "clear_queue?guid=G" ), bool )
    assert isinstance( fling( "clear_queue?guid=G2" ), bool )
    response = fling( "queue?guid=G" )
    assert response["total_items"] == 0
    response = fling( "queue?guid=G2" )
    assert response["total_items"] == 0

def basic_tests():

    print "== basic_tests =="

    # clear all devices from this network.
    clean()
    
    # verify lookup sees no devices.
    response = fling("lookup")
    assert len(response["services"]) == 0
    assert response["yourip"]
    assert isinstance(response["interval"], int)
    assert response["interval"] > 0
    ip = response["yourip"]
    
    # verify has_services returns false.
    assert not fling("has_services")
    assert not fling("has_devices")
    
    # announce a test device.
    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )
    assert response["yourip"] == ip
    assert isinstance(response["interval"], int)
    assert response["interval"] > 0
    
    # lookup to verify it is discoverable.
    response = fling( "lookup" )
    #{
    #  "services": [
    #    {
    #      "name": "test service", 
    #      "service": "", 
    #      "model_id": "test", 
    #      "external_ip": "99.131.183.170", 
    #      "version": "1", 
    #      "t": 1295739793, 
    #      "guid": "G", 
    #      "port": 0
    #    }
    #  ], 
    #  "yourip": "99.131.183.170", 
    #  "version": "1.0", 
    #  "interval": 900
    #}
    
    services = response["services"]
    assert len(services) == 1
    assert services[0]["guid"] == "G"
    assert services[0]["name"] == "test service"
    assert services[0]["version"] == "1"
    assert services[0]["model_id"] == "test"
    assert response["interval"] > 0
    assert response["yourip"]
    
    # verify has_services returns true.
    assert fling("has_services")
    assert fling("has_devices")
    
    # clear the queue of any items that might exist from a previous test.
    clear_queues()
    
    # fling an item.
    # http://flingo.tv/fling/fling?[url=U | deofuscator=D&context=C]
    #   [&guid=G&title=T&description=D&image=I&preempt=P]

    # we create a random URL to ensure with good probability that the content
    # has never before been placed in the content database.  This exercises
    # different code paths in the backend then if the content had been seen.
    mp4_url = u"http://example.com/foo%s.mp4" % randhex()
    assert fling( "fling?url=" + quote( mp4_url ) +
        "&title=Foo&image=" + quote( "http://example.com/foo.jpg" ) +
        "&description=The+best+movie+ever." )

    # verify it is in the queue.
    response = fling( "queue?guid=G" )
    assert response["total_items"] == 1
    items = response["items"]
    assert len(items) == 1
    item = items[0]
    assert item["description"] == "The best movie ever."
    assert item["title"] == "Foo"
    assert item["encodings"][0]["url"] == mp4_url 
    
    # clear the queue on the test devices.
    assert fling( "clear_queue?guid=G" )
    response = fling( "queue?guid=G" )
    assert response["total_items"] == 0
    
    # announce a second device.
    assert fling( "announce?guid=G2&model_id=test" +
        "&name=test2&service=S&version=1" )
    
    # verify both devices are now discoverable.
    response = fling( "lookup" )
    services = response["services"]
    assert len(services) == 2, "Fail lookup with 2 (1)" 
    assert ((services[0]["name"] == "test service" and 
             services[1]["name"] == "test2") or
            (services[1]["name"] == "test service" and 
             services[0]["name"] == "test2"))
    assert ((services[0]["guid"] == "G" and services[1]["guid"] == "G2") or
             (services[1]["guid"] == "G" and services[0]["guid"] == "G2"))
    
    # fling to both devices.
    response = fling( "fling?url=" + quote( "http://example.com/foo.mp4" ) +
        "&title=Foo&image=" + quote( "http://example.com/foo.jpg" ) +
        "&description=The+best+movie+ever.")
    assert response
    
    # verify the item is in both queues.
    response = fling( "queue?guid=G" )
    assert response["total_items"] == 1
    items = response["items"]
    assert len(items) == 1
    item = items[0]
    assert item["description"] == "The best movie ever."
    assert item["title"] == "Foo"
    assert item["encodings"][0]["url"] == u'http://example.com/foo.mp4' 
    
    response = fling( "queue?guid=G2" )
    assert response["total_items"] == 1
    items = response["items"]
    assert len(items) == 1
    item = items[0]
    assert item["description"] == "The best movie ever."
    assert item["title"] == "Foo"
    assert item["encodings"][0]["url"] == u'http://example.com/foo.mp4' 
    
    clear_queues()  # clear queues before testing fling to a single device.
    
    # fling to a single device.
    assert fling( "fling?url=" + quote( "http://example.com/foo.mp4" ) +
        "&title=Foo&image=" + quote( "http://example.com/foo.jpg" ) +
        "&description=The+best+movie+ever.&guid=G" )
    
    # verify the item only appears in the single device.
    response = fling( "queue?guid=G" )
    assert response["total_items"] == 1
    assert response["items"][0]["title"] == "Foo"
    
    response = fling( "queue?guid=G2" )
    assert response["total_items"] == 0
    
    # fling using POST
    params = {
      "url" : "http://example.com/foo.mp4",
      "title" : "Foo",
      "image" : "http://example.com/foo.jpg",
      "description" : "The best movie ever.",
      "guid" : "G2"
    }
    response = fling( "fling", post=True, **params )
    assert response
    
    # get queue using POST of application/x-www-form-urlencoded body.
    request = urllib2.Request( FLING_ADDR_BASE + "/fling/queue", "guid=G2" )
    response = json.loads(urllib2.urlopen(request).read())
    assert response["total_items"] == 1
    assert response["items"][0]["title"] == "Foo"
    
    # get queue using JSON-RPC.
    response = fling( "queue", guid = u"G2", post=True )
    assert response["total_items"] == 1
    assert response["items"][0]["title"] == "Foo"

    # clear all devices from this network and clear their queues.
    clean()
    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    # fling same item twice and the queue should have two items with the same
    # uuid.
    params = {
      "url" : "http://example.com/foo.mp4",
      "title" : "Foo",
      "image" : "http://example.com/foo.jpg",
      "description" : "The best movie ever.",
    }
    assert fling( "fling", **params )
    assert fling( "fling", **params )
    response = fling( "queue", guid = u"G", post=True )
    assert response["total_items"] == 2
    assert response["items"][0]["title"] == "Foo"
    assert response["items"][1]["title"] == "Foo"
    #print "items[1]=", response["items"][1]
    guid = response["items"][0]["guid"]
    assert guid == response["items"][1]["guid"]
    
    # fling same item to another device and the queue should have an item
    # with the same guid.
    response = fling( "announce?guid=G2&model_id=test&name=test+service" +
        "&service=S&version=1" )
    params["guid"] = "G2"
    assert fling( "fling", **params )
    response = fling( "queue", guid = u"G2", post=True )
    assert response["total_items"] == 1
    assert guid == response["items"][0]["guid"] 

    clear_queues()  # clear queues before testing fling to a single device.
    params = {
      "url" : u"http://example.com/pi\u00f1on.mp4",
      "title" : u"Pi\u00f1on",
      "image" : u"http://example.com/pi\u00f1on.jpg",
      "description" : u"The best movie about Pi\u00f1on trees.",
    }
    assert fling( "fling", **params )
    response = fling( "queue?guid=G" )
    assert response["total_items"] == 1
    items = response["items"]
    assert len(items) == 1
    item = items[0]
    assert item["title"] == u"Pi\u00f1on"
    assert item["description"] == u"The best movie about Pi\u00f1on trees."
    assert item["encodings"][0]["url"] == u"http://example.com/pi\u00f1on.mp4" 

    clear_queues()  # clear queues before testing fling to a single device.
    response = fling( "fling", post=True, **params )
    response = fling( "queue?guid=G" )
    assert response["total_items"] == 1
    items = response["items"]
    assert len(items) == 1
    item = items[0]
    assert item["title"] == u"Pi\u00f1on"
    assert item["description"] == u"The best movie about Pi\u00f1on trees."
    assert item["encodings"][0]["url"] == u"http://example.com/pi\u00f1on.mp4" 

    clean()

def error_tests():    
    print "== error_tests =="
    clean()
    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )
    try:
        # should be invalid because no url.
        fling( "fling?title=pathology+test&url=" )
        assert False, "should raise exception for empty url"
    except Fault, f:
        assert f.faultCode == VALUE_ERROR

    try:
        fling( "fling?title=pathology+test" )
        assert False, "should raise exception for missing url"
    except Fault, f:
       assert f.faultCode == VALUE_ERROR

    try:
        fling( "fling?title=pathology+test&url=" + quote( "http:/invalid" ) )
        assert False, "should raise exception for invalid url"
    except Fault, f:
        assert f.faultCode == VALUE_ERROR

    try:
        fling("fling?title=pathology+test&image=htttt&url=" +
            quote( "http://foo.com/a.mp4" ) )
        assert False, "should raise exception for invalid image URL"
    except Fault, f:
        assert f.faultCode == VALUE_ERROR

    clean()

def test_1af(): 
    print "== test_1af =="
    clean()

    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    # test zero arg fling. (passes referer URI to metadizer)
    # Note: this won't work with the fling call because it is "restricted."
    # To test zero arg fling, I have to go through the "a" calls.
    #assert fling( "fling", referer = "http://flingo.org" )
    #response = fling( "queue", "guid" = u"G" )
    #assert response["total_items"] == 1
    #assert response["items"][0]["title"] == "Big Buck Bunny"
    #guid = response["items"][0]["guid"]

    # test one arg fling (passes purl to metadizer)
    assert fling( "fling", purl = u"http://flingo.org" )
    assert fling( "fling", purl = u"http://flingo.org" )
    response = fling( "queue", guid = u"G" )
    assert response["total_items"] == 2
    assert response["items"][1]["title"] == "Big Buck Bunny"
    assert response["items"][0]["guid"] == response["items"][1]["guid"]

    clean()

def call_tests():
    print "== call_tests =="
    clean()

    # announce a test device.
    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )
    assert isinstance(response["interval"], int)
    assert response["interval"] > 0

    assert call( "ping", {} )
    d = call( "echo", { "s" : "hello world" } )
    assert d["s"] == "hello world"
    
    d = call( "echo", { "x" : None } )
    assert d["x"] == None
    
    d = call( "echo", { "x" : 10 } )
    assert d["x"] == 10
    
    d = call( "echo", { "x" : 10, "y" : "foo" } )
    assert d["x"] == 10
    assert d["y"] == "foo"
    
    d = call( "echo", { "x" : [1,2,4,"blah"] } )
    assert isinstance(d["x"],list)
    assert d["x"] == [1,2,4,"blah"]
    
    assert call( "echox", { "x" : 10 } ) == 10
    assert call( "echox", { "x" : "hello world" } ) == "hello world"
    assert call( "echox", { "x" : [1,2,4,"blah"] } ) == [1,2,4,"blah"]
    d = call( "echox", { "x" : { "a" : 10, "b" : [1, "foo"] } })
    assert d["a"] == 10
    assert d["b"] == [1,"foo"]
    
    try:
        call( "raise_exception", {} )
    except Fault, f:
        assert f.faultString == "hi there"
    
    try:
        call( "raise_fault", {} )
    except Fault, f:
        assert f.faultCode == 9999
        assert f.faultString == "hi there"
    
    try:
        call( "return_fault", {} ) 
    except Fault, f:
        assert f.faultCode == 9999
        assert f.faultString == "hi there"
    
    assert call( "return_nothing", {} ) == None

    try:
        call( "sleep", { "secs" : 5 }, ttl=1 )
    except HTTPError, e:
        assert e.getcode() == 503


def referer_tests():
    print "== referer_tests =="

    # clear all devices from this network.
    clean()

    # announce a test device.
    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    # test lookup with flingo.tv referer.
    # curl --referer "http://flingo.tv/foo" "http://dave.flingo.tv/fling/lookup"
    r = fling("lookup", referer="http://%s/foo" % DOMAIN)
    assert "services" in r, r
    assert len(r["services"]) > 0
    for s in r["services"]:
      #print "s=", s
      if s["guid"] == "G":
        break
    else:
      assert False, "guid not found in lookup"

    # test lookup with referer that includes the port number.  Some 
    # platforms (including stagecraft on the broadcom 3594), include the
    # port number in the Hostname header even when it is port 80.
    r = fling("lookup", referer="http://%s:80/foo" % DOMAIN)
    assert "services" in r, r
    assert len(r["services"]) > 0
    for s in r["services"]:
      if s["guid"] == "G":
        break
    else:
      assert False, "guid not found in lookup"


    # test lookup with some other referer with path and without path in URL.
    r = fling("lookup", referer="http://foo.com/boo")
    assert "services" in r, r
    assert len(r["services"]) > 0
    for s in r["services"]:
      assert "guid" not in s, s
    
    r = fling("lookup", referer="http://foo.com/")
    assert "services" in r, r
    assert len(r["services"]) > 0
    for s in r["services"]:
      assert "guid" not in s, s
    
    r = fling("lookup", referer="http://foo.com")
    assert "services" in r
    assert len(r["services"]) > 0
    for s in r["services"]:
      assert "guid" not in s, s
    
    # test lookup with crunchyroll (crunchyroll is whitelisted).
    r = fling("lookup", referer="http://crunchyroll.com/bar")
    assert "services" in r, r
    assert len(r["services"]) > 0
    for s in r["services"]:
      if s["guid"] == "G":
        break
    else:
      assert False, "guid not found in lookup"
    
    # test lookup with youtubesocial.com (youtubesocial is whitelisted).
    r = fling("lookup", referer="http://youtubesocial.com/bar")
    assert "services" in r, r
    assert len(r["services"]) > 0
    for s in r["services"]:
      if s["guid"] == "G":
        break
    else:
      assert False, "guid not found in lookup"
    
    # test fling and queue.
    try:
        r = fling(u"fling", guid = u"G", title = u"Foopie", 
             description = u"Hello World", 
             url = u"http://foo.com/foopie.mp4", 
             image = u"http://foo.com/foo.png", referer="http://foo.com/a")
        assert False, "Should raise fault"
    except Fault, f:
        assert f.faultCode == 609
        assert "Invalid Referrer" in f.faultString     


def push_front_back_tests():
    print( "== push_front_back_tests ==" )

    # clear all devices from this network.
    clean()

    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    response = fling( "clear_queue", guid = u"G" )
    response = fling( "queue", guid = u"G" )
    assert len(response["items"]) == 0

    # fling to both devices.
    response = fling( "fling", 
          url = "http://example.com/foo.mp4",
          title = "Foo", image = "http://example.com/foo.jpg",
          description = "The best movie ever.",
          front = False )
    assert response

    response = fling( "fling",
          url = "http://example.com/abc.mp4",
          title = "Sifu", image = "http://example.com/sifu.jpg",
          description = "The master.",
          front = False  )
    assert response

    response = fling( "queue", guid = "G" )
    assert len(response["items"]) == 2
    #print "items", response["items"][0]
    assert ( response["items"][0]["encodings"][0]["url"] == 
             "http://example.com/foo.mp4" )
    assert ( response["items"][1]["encodings"][0]["url"] == 
             "http://example.com/abc.mp4" )
    
    response = fling( "fling",
         url = "http://example.com/blu.mp4",
         title = "Blu", image = "http://example.com/blu.jpg",
         description = "For those who cannot spell primary colors.",
         front = True )
    assert response

    response = fling( "queue", guid = u"G" )
    assert len(response["items"]) == 3
    assert ( response["items"][0]["encodings"][0]["url"] == 
             "http://example.com/blu.mp4" )
    assert ( response["items"][1]["encodings"][0]["url"] == 
             "http://example.com/foo.mp4" )
    assert ( response["items"][2]["encodings"][0]["url"] == 
             "http://example.com/abc.mp4" )

    clean()


def form_tests():
    print "== form_tests =="
    clean()

    r = get( "fling/a", title="Foo Bar", description="This is a description",
         url="http://example.com/foo.mp4", 
         purl="http://example.com/foo.html" )
    
    # confirm result is HTML.  It was already confirmed 
    assert r.find( "<html" ) != -1 or r.find( "<HTML" ) != -1
    assert r.find( "<body>" ) != -1 or r.find( "<BODY>" ) != -1
    assert r.find( "Fling can play" ) != -1

    response = fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    r = get( "fling/a", title="Foo Bar", description="This is a description",
         url="http://example.com/foo.mp4", 
         purl="http://example.com/foo.html" )
    
    # confirm result is HTML.  It was already confirmed 
    assert r.find( "<html" ) != -1 or r.find( "<HTML" ) != -1
    assert r.find( "<body>" ) != -1 or r.find( "<BODY>" ) != -1
    
    # confirm it is the "fling" form. The following tests are quite fragile, 
    # but if I run the unit tests frequently, I will see this test break and I 
    # can update the text below before there is large divergence.  --Dave
    assert r.find( "Fling this video" ) != -1
    assert r.find( "Foo Bar" ) != -1
    assert r.find( "foo.mp4" ) != -1
    assert r.find( "This is a description" ) != -1
    
    # zero-arg fling form.
    r = get( "fling/a", referer = "http://flingo.org" )
    assert r.find( u"Big Buck Bunny" ) != -1
    
    # 1-arg fling form.
    r = get( "fling/a", purl = "http://flingo.org" )
    assert r.find( u"Big Buck Bunny" ) != -1
    
    r = form_post( "fling/a_form", referer = u"http://flingo.tv/fling/a", 
                   title = u"Foo Bar", action = u"push_back", 
                   url = u"http://example.com" )
    assert r.find( u"This video has been flung" ) != -1
    

    fling( "clear_queue", guid = u"G" )

    # test a_form restrict_referer.  A missing referer header is ok.
    r = form_post( "fling/a_form", title = u"Foo Bar", action = u"push_back", 
                   url = u"http://example.com/a.mp4" )
    assert r.find( u"This video has been flung" ) != -1
    r = fling( "queue", guid = u"G", index = 0, howmany = 1000 )    

    assert r["total_items"] == 1
    assert r["items"][0]["title"] == u"Foo Bar"
    assert len(r["items"][0]["encodings"]) == 1
    assert r["items"][0]["encodings"][0]["url"] == u"http://example.com/a.mp4"

    # test bad conditions.
    # - missing action.
    try:
        r = form_post( "fling/a_form", title = u"Foo Bar", 
                       url = u"http://example.com/a.mp4" )
        assert False, "Should have generated an HTTPError exception."
    except HTTPError, e: 
        pass

    # - no url.
    r = form_post( "fling/a_form", title = u"Foo Bar", 
                   action = u"push_back" )
    assert r.find( "cannot be flung" ) != -1
    assert r.find( "Must provide page url" ) != -1  # referer, content URL,...

    # verify that queue still contains 1 item and it is "Foo Bar"
    r = fling( "queue", guid = u"G", index = 0, howmany = 1000 )    

    assert r["total_items"] == 1
    assert r["items"][0]["title"] == u"Foo Bar"
    assert len(r["items"][0]["encodings"]) == 1
    assert r["items"][0]["encodings"][0]["url"] == u"http://example.com/a.mp4"

    clean()

def test_metadizer():
    clean()

    fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    r = fling( "metadize", purl = "http://flingo.org" )
    assert r["image"] == "http://flingo.org/images/BigBuckBunny.jpg"
    assert r["page_url"] == "http://flingo.org"
    assert r["encodings"][0]["uri"].endswith("BigBuckBunny_640x360.m4v")

    r = fling( "metadize", referer = "http://flingo.org" )
    assert r["image"] == "http://flingo.org/images/BigBuckBunny.jpg"
    assert r["page_url"] == "http://flingo.org"
    assert r["encodings"][0]["uri"].endswith("BigBuckBunny_640x360.m4v")

    # test youtube.    
    r = fling( "metadize", purl = "http://www.youtube.com/watch?v=GI5Nmi6_iPY" )
    assert r["title"] == "Test Fling"
    assert r["context"] == "http://www.youtube.com/watch?v=GI5Nmi6_iPY"
    assert r["page_url"] == "http://www.youtube.com/watch?v=GI5Nmi6_iPY"
    assert r["external_id"] == "GI5Nmi6_iPY"    
    assert ( r["deobfuscator"].endswith( 
      "flingo.tv/swf/youtube/YouTubeDeobfuscator.swf" ))
    assert r["image"] == "http://i.ytimg.com/vi/GI5Nmi6_iPY/hqdefault.jpg"

    r = get( "fling/a", purl = "http://www.youtube.com/watch?v=GI5Nmi6_iPY" )
   
    assert r.find( "<html" ) != -1 or r.find( "<HTML" ) != -1
    assert r.find( "<form" ) != -1 or r.find( "<FORM" ) != -1
    assert r.find( "Test Fling" ) != -1
    assert r.find( "http://i.ytimg.com/vi/GI5Nmi6_iPY/hqdefault.jpg" ) != -1
    assert r.find( "fling from a web site to any flingo-enabled TV" ) != -1

    r = get( "fling/a", referer = "http://www.youtube.com/watch?v=GI5Nmi6_iPY" )
    assert r.find( "<html" ) != -1 or r.find( "<HTML" ) != -1
    assert r.find( "<form" ) != -1 or r.find( "<FORM" ) != -1
    assert r.find( "Test Fling" ) != -1
    assert r.find( "http://i.ytimg.com/vi/GI5Nmi6_iPY/hqdefault.jpg" ) != -1
    assert r.find( "fling from a web site to any flingo-enabled TV" ) != -1

    # test both URL and page URL.
    r = get( "fling/a", purl = "http://flingo.org", 
             url = u"http://d3cqjei15bh7c8.cloudfront.net/"
                    "BigBuckBunny_640x360.m4v" )
    assert r.find( "<html" ) != -1 or r.find( "<HTML" ) != -1
    assert r.find( "<form" ) != -1 or r.find( "<FORM" ) != -1
    assert r.find( "Big Buck Bunny" ) != -1
    assert r.find( "BigBuckBunny_640x360.m4v" ) != -1

    # test both URL and referer
    r = get( "fling/a", referer = "http://flingo.org", 
             url = u"http://d3cqjei15bh7c8.cloudfront.net/"
                    "BigBuckBunny_640x360.m4v" )
    assert r.find( "<html" ) != -1 or r.find( "<HTML" ) != -1
    assert r.find( "<form" ) != -1 or r.find( "<FORM" ) != -1
    assert r.find( "Big Buck Bunny" ) != -1
    assert r.find( "BigBuckBunny_640x360.m4v" ) != -1

    clean()

def test_ephemeral():
    clean()

    fling( "announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    try:
        # ephemeral URL alone is not enough to fling.  We need to provide
        # enough to create an external ID.  Something ephemeral is not appropriate
        # for such an ID.
        r = fling( "fling", eurl = "http://example.com/foo.mp4" )
        assert False, "Should raise exception."
    except Fault, f:
        assert f.faultCode == VALUE_ERROR

    fling( "fling", eurl = "http://example.com/foo.mp4",
           purl = "http://example.com/foo.html", title = "Foo" )
    r = fling( "queue", guid = u"G" )
    assert r["total_items"] == 1
    assert r["items"][0]["title"] == "Foo"
    encoding = r["items"][0]["encodings"][0]
    assert encoding["url"] == "http://example.com/foo.mp4"
    assert encoding["is_ephemeral"]

    fling( "clear_queue", guid = u"G" )

    fling( "fling", eurl = "http://youtube.com/foo.mp4",
           purl = "http://www.youtube.com/user/flingotv" )
    r = fling( "queue", guid = u"G" )
    
    assert r["total_items"] == 1
    assert r["items"][0]["title"] == u"Flingo Demo"
    encoding = r["items"][0]["encodings"][0]
    assert encoding["url"] == u"http://youtube.com/foo.mp4"
    assert encoding["is_ephemeral"]

    fling( "clear_queue", guid = u"G" )

    r = form_post( "fling/a_form", referer = u"http://flingo.tv/fling/a", 
            title = u"Flingo Demo", action = u"push_back", 
            eurl = u"http://youtube.com/foo.mp4",
            purl = u"http://www.youtube.com/user/flingotv" )
    r = fling( "queue", guid = u"G" )
    assert r["total_items"] == 1
    assert r["items"][0]["title"] == u"Flingo Demo"
    assert r["items"][0]["encodings"][0]["url"] == u"http://youtube.com/foo.mp4"
    assert r["items"][0]["encodings"][0]["is_ephemeral"] == True

    clean()

def test_get_next():

    clean()

    # items that are flung should appear "up next."

    fling( u"announce?guid=G&model_id=test&name=test+service" +
        "&service=S&version=1" )

    r = api(u"get_next", guid=u"G", model_id=u"test", version=u'1' )
    assert r["total_items"] == 4

    fling( "fling", url = u"http://example.com/foo.mp4",
           purl = u"http://example.com/foo.html", title = u"Foo" )
    r = fling( "queue", guid = u"G" )
    assert r["total_items"] == 1
    assert r["items"][0]["title"] == u"Foo"
    encoding = r["items"][0]["encodings"][0]
    assert encoding["url"] == "http://example.com/foo.mp4"
    
    r = api(u"get_next", guid=u"G", model_id=u"test", version=u'1' )
    assert r["total_items"] == 4
    assert r["items"][0]["title"] == u"Foo"
    assert r["items"][0]["encodings"][0]
    assert encoding["url"] == "http://example.com/foo.mp4"

    clean()


if __name__ == "__main__":

    print """
== Flingo API Unit Tests ==

These unit test the Flingo API calls.  Since these tests are run from
a command-line rather than a browser, these test the behavior only as
seen by applications running outside a browser.

NOTE: These unit tests clear all your devices from the flingo.tv
discovery service.  The only effect is that the devices will
temporarily not be discoverable from web sites.  These tests will not
affect the state internal to these applications such as favorites,
bookmarks, queue, etc.  You may have to restart Flingo appliations or
devices for them to once again be discoverable.
"""
    
    rpc = RPCServer()
    
    gevent.spawn(handler, "G")
    gevent.spawn(handler, "G2")
    update_event = gevent.event.Event()
    fail_event = gevent.event.Event()

    basic_tests()
    error_tests()
    test_1af()
    call_tests() 
    referer_tests()
    push_front_back_tests()
    form_tests()
    test_metadizer()
    test_ephemeral()
    test_get_next()
    
    assert fling("clear")
    assert call( "done", {} )
    
    print "Passed all tests."



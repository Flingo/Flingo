#!/usr/bin/env python

import datetime                              
log_file = open( "/tmp/remote_control.log", "a")
# easier to use local time.                                               
iso = lambda : datetime.datetime.now().isoformat()
#iso = lambda : datetime.datetime.utcnow().isoformat()
def log(s):
    log_file.write( "%s: %s\n" % (iso(), s) )
    log_file.flush()

log( "starting" )

try:
    import json
except ImportError:
    import simplejson as json

import BaseHTTPServer
import httplib
import os
from sha import sha
import socket
from threading import Timer
import traceback
from urlparse import urlparse
from uuid import getnode as get_mac


# If false then the remote control functions are not available as HTTP GET.
# The problem with changing state in response to a GET request is that it
# doesn't adhere to REST.  It also allows for web pages or other parties
# to change the state of the TV based on a GET.  A GET is much easier
# for a browser to generate than a POST.  For example, a link on a page
# generates a GET request.
convenience_get = True
nav_controls = set([ "up", "down", "left", "right",
                     "ok", "enter", "back", "home"])
playback_controls = set([ "stop", "play", "pause", "ff", "rev", "fling" ])
other_controls = set(["power", "next", "prev", "search", "eject", "option"])

AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_6) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1" 

description = "WDTV Live Plus"
model = model_id = "WDBABX0000"


class FlingRemoteControlHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Basic remote control functions.

      Navigation functions:
    
      POST http://192.168.1.127:8080/up
      POST http://../down
      POST http://../left
      POST http://../right
      POST http://../enter
      POST http://../ok     # same as enter for WD TV.
      POST http://../back
      POST http://../home

      Playback functions:

      POST http://../stop
      POST http://../play
      POST http://../pause
      POST http://../ff
      POST http://../rev     # rewind.

      Other functions:

      POST http://../power
      POST http://../next
      POST http://../prev
      POST http://../search
      POST http://../eject
      """

    def do_GET(self):
        #print "do_GET"

        # when true, "convenience_get" violates REST.  It allows
        # HTTP GETs to perform operations that change the state of the
        # TV.
        if convenience_get:
            self.process_request()


    def do_POST(self):

        # You can create a post with an empty body by doing:
        #  curl "http://192.168.1.49:8000/up" --data ""
        #print "do_POST"
        self.process_request()

    def process_request(self):
        #print " client_address: ", self.client_address
        #print " command: ", self.command
        #print " path:", self.path
        #print " headers:", self.headers
    
    
        # ex:  /foo?x=10&y=11
        print "parsing headers"
        lst = self.path.split("?")
        if len(lst) == 1:
            cmd, kwargs = self.path[1:], { }
        else:
            cmd, kwargs = lst[0][1:], lst[1]
            kwargs = dict([kv.split("=") for kv in kwargs.split("&")])
    
        print "Calling remote"
        if not self.do_remote(cmd, kwargs):
            self.wfile.write( "HTTP/1.1 404 Not Found\n")
            self.end_headers()
        else:
            #HERE. WTF! --Dave
            #self.send_response(200)  # causes seg fault.
            self.wfile.write( "HTTP/1.1 200 OK\n")  # in lieu of line above.
            
            result = 'true'  # result = json.dumps(True)
        
            # enable JSONP.  This makes the remote control sandbox-reachable
            # using the script tag.
            if "callback" in kwargs:
                result = "%s(%s)" % (kwargs["callback"], result)

            self.send_header("Content-Type","application/json")
            
            self.send_header( "Content-Length", len(result) )
            self.end_headers()
            self.wfile.write(result)
    
    def do_remote(self, cmd, kwargs):
        print "do_remote called with cmd %s and kwargs=%s" % (cmd,kwargs)
        log( "do_remote called with cmd %s and kwargs=%s" % (cmd,kwargs) )
        if cmd in nav_controls:
            if cmd == "up":
                open("/tmp/ir_injection", "w").write("u")
            elif cmd == "down":
                open("/tmp/ir_injection", "w").write("d")
            elif cmd == "left":
                open("/tmp/ir_injection", "w").write("l")
            elif cmd == "right":
                open("/tmp/ir_injection", "w").write("r")
            elif cmd == "ok" or cmd == "enter":
                open("/tmp/ir_injection", "w").write("n")
            elif cmd == "back":
                open("/tmp/ir_injection", "w").write("T")
            elif cmd == "home":
                open("/tmp/ir_injection", "w").write("o")
            else:
                return False
        elif cmd in playback_controls:
            if cmd == "stop":
                open("/tmp/ir_injection", "w").write("t")
            elif cmd == "play" or cmd == "fling":
                url = kwargs.get("url")
                print "play url:", url
                if url:
                    os.system( "upnp-cmd SetAVTransportURI %s" % kwargs["url"])
                    print "playing %s" % kwargs["url"] 
                    os.system( "upnp-cmd Play" )
                else:
                    open("/tmp/ir_injection", "w").write("p")
            elif cmd == "pause":
                #open("/tmp/ir_injection", "w").write("p")
                os.system( "upnp-cmd Pause" )  # avoids toggle play/pause
            elif cmd == "ff":   # fast-forward
                print "injecting fast foward: 'I'"
                open("/tmp/ir_injection", "w").write("I")
            elif cmd == "rev":  # rewind
                print "injecting rewind 'H'"
                open("/tmp/ir_injection", "w").write("H")
            else:
                return False
        elif cmd in other_controls:
            if cmd == "power":
                open("/tmp/ir_injection", "w").write("w")
            elif cmd == "next":  
                open("/tmp/ir_injection", "w").write("]")
            elif cmd == "prev":  
                open("/tmp/ir_injection", "w").write("[")
            elif cmd == "search": 
                open("/tmp/ir_injection", "w").write("E")
            elif cmd == "eject": 
                open("/tmp/ir_injection", "w").write("X")
            elif cmd == "options": 
                open("/tmp/ir_injection", "w").write("G")
            return False
        else:
            return False
        return True
    
def request(url, body = None):
    global AGENT
    (scheme, netloc, path, pars, query, fragment) = urlparse(url)
    lst = netloc.split(":")
    if len(lst) == 2:
        host, port = lst
    else:
        host, port = lst[0], 80
  
    print "host", host
    conn = httplib.HTTPConnection(netloc, port)
  
    # http://foo.com/a/b/c?do=blah&po=fa --> /foo.com/a/b/c?do=blah&po=fa
    long_path = "/" + "/".join(url.split("/")[3:])
  
    print "long_path=", long_path
    if body:
        headers = {"Content-type": "application/json",
                   "Accept": "application/json"}

        body = json.dumps(body)
        conn.request("POST", long_path, body, headers )
    else:
        conn.request("GET", long_path, headers = { "User-Agent" : AGENT } )
  
    r = conn.getresponse()
    if r.status != 200:
      raise Exception( "** wget encountered error. returned status: %s %s" % (
        r.status, r.reason ))
    return r

def guid():
    return sha("%s" % get_mac()).digest().encode("hex")

def private_ip():

    # If private_ip() is run during the boot process of the WD then I get
    # "no address associated with hostname" error.  It may just be too early
    # in the boot process. 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("flingo.tv",80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def announce():
    global t
    try:
        try:
            log( "announcing" )
            r = request( "http://flingo.tv/fling/announce", 
                {
                  "name" : "remote_control",
                  "guid" : guid(),
                  "service" : "remote_control",
                  "description" : "Service that provides analogous "
                                  "functionality to a remote control.",
                  "make" : "western_digital",
                  "model" : model,
                  "model_id" : model,
                  "platform" : "wd_sigma",
                  "private_ip" : ["%s:8000" % private_ip()],
                  "dev_description" : description,
                  "version" : "1.0"
                } )   
            print r
        except:
            s = traceback.format_exc()
            log(s)
    finally:
        # announces every 30 seconds.  A little overkill, but who cares.
        # It is just a demo.
        t.cancel()
        t = Timer(30, announce)
        t.start()
   


def run(server_class=BaseHTTPServer.HTTPServer,
        handler_class=FlingRemoteControlHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    log( "serve_forever" )
    httpd.serve_forever()



# announces service to fling.
# It announces a "remote_control" service.  A remote_control service
if __name__ == "__main__":
    try:
        try:
            log( "scheduling announce for 10 seconds after start." )
            t = Timer(10, announce )
            t.start()
            log( "calling run" )
            run()
        except:
            s = traceback.format_exc()
            log(s)
    finally:
        log( "exiting..." )

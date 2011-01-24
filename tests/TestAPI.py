# Copyright(c) 2011. Free Stream Media Corp. Released under the terms
# of the GNU General Public License version 2.0.
#
# These test the API separately from any given application.
#
# Author: David Harrison

import urllib
import urllib2
from urllib2 import Request
from urllib import quote
import json
import sys

print """
== Flingo API Unit Tests ==

These unit test the Flingo API calls.  Since these tests are run from
a command-line rather than a browser, these test the behavior only 
as seen by applications running outside a browser.  

NOTE: These unit tests clear all your devices from the flingo.tv discovery 
service.  The only effect is that the devices will temporarily not 
be discoverable from web sites.  These tests will not affect the state 
internal to these applications such as favorites, bookmarks, queue, etc.
You may have to restart Flingo appliations or devices 
for them to once again be discoverable.
"""

FLING_ADDR_BASE = 'http://dave.flingo.tv'

def call( f, kwargs = None):
    url = FLING_ADDR_BASE + '/fling/' + f
    if kwargs:
        if isinstance( kwargs, dict ):
            kwargs = urlencode( kwargs )
        url += "?" + kwargs
    print "calling: " + url
    req = urllib2.Request(url)
    return json.loads(urllib2.urlopen(req).read())

# clear all devices from this network.
assert call("clear")

# verify lookup sees no devices.
response = call("lookup")
assert len(response["services"]) == 0
assert response["yourip"]
assert isinstance(response["interval"], int)
assert response["interval"] > 0
ip = response["yourip"]

# verify has_services returns false.
assert not call("has_services")
assert not call("has_devices")

# announce a test device.
response = call( "announce?guid=G" +
    "&model_id=abadbabeeeabadbabeeeabadbabeeeabadbabeee&name=test" +
    "&service=S&version=1" )
assert response["yourip"] == ip
assert isinstance(response["interval"], int)
assert response["interval"] > 0

# lookup to verify it is discoverable.
response = call( "lookup" )
#{
#  "services": [
#    {
#      "name": "test", 
#      "service": "", 
#      "model_id": "abadbabeeeabadbabeeeabadbabeeeabadbabeee", 
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
assert services[0]["name"] == "test"
assert services[0]["version"] == "1"
assert services[0]["model_id"] == "abadbabeeeabadbabeeeabadbabeeeabadbabeee"
assert response["interval"] > 0
assert response["yourip"]

# verify has_services returns true.
assert call("has_services")
assert call("has_devices")

# clear the queue of any items that might exist from a previous test.
assert isinstance( call( "clear_queue?guid=G" ), bool )
assert isinstance( call( "clear_queue?guid=G2" ), bool )

# fling an item.
# http://flingo.tv/fling/fling?[url=U | deofuscator=D&context=C]
#   [&guid=G&title=T&description=D&image=I&preempt=P]
assert call( "fling?url=" + quote( "http://example.com/foo.mp4" ) +
    "&title=Foo&image=" + quote( "http://example.com/foo.jpg" ) +
    "&description=The+best+movie+ever." )

# verify it is in the queue.
response = call( "queue?guid=G" )
assert response["total_items"] == 1
items = response["items"]
assert len(items) == 1
item = items[0]
assert item["description"] == "The best movie ever."
assert item["title"] == "Foo"
assert item["encodings"][0]["url"] == u'http://example.com/foo.mp4' 

# clear the queue on the test devices.
assert call( "clear_queue?guid=G" )
response = call( "queue?guid=G" )
assert response["total_items"] == 0

# announce a second device.
assert call( "announce" +
    "?guid=G2&model_id=abadbabeeeabadbabeeeabadbabeeeabadbabeee&name=test2" +
    "&service=S&version=1" )

# verify both devices are now discoverable.
response = call( "lookup" )
services = response["services"]
assert len(services) == 2, "Fail lookup with 2 (1)" 
assert ((services[0]["name"] == "test" and services[1]["name"] == "test2") or
        (services[1]["name"] == "test" and services[0]["name"] == "test2"))
assert ((services[0]["guid"] == "G" and services[1]["guid"] == "G2") or
         (services[1]["guid"] == "G" and services[0]["guid"] == "G2"))

# fling to both devices.
response = call( "fling?url=" + quote( "http://example.com/foo.mp4" ) +
    "&title=Foo&image=" + quote( "http://example.com/foo.jpg" ) +
    "&description=The+best+movie+ever.")
assert response


# verify the item is in both queues.
response = call( "queue?guid=G" )
assert response["total_items"] == 1
items = response["items"]
assert len(items) == 1
item = items[0]
assert item["description"] == "The best movie ever."
assert item["title"] == "Foo"
assert item["encodings"][0]["url"] == u'http://example.com/foo.mp4' 

response = call( "queue?guid=G2" )
assert response["total_items"] == 1
items = response["items"]
assert len(items) == 1
item = items[0]
assert item["description"] == "The best movie ever."
assert item["title"] == "Foo"
assert item["encodings"][0]["url"] == u'http://example.com/foo.mp4' 

# clear queues before testing fling to a single device.
response = call( "clear_queue?guid=G" )
assert response

response = call( "queue?guid=G" )
assert response["total_items"] == 0
assert call( "clear_queue?guid=G2" )

response = call( "queue?guid=G2" )
assert response["total_items"] == 0

# fling to a single device.
assert call( "fling?url=" + quote( "http://example.com/foo.mp4" ) +
    "&title=Foo&image=" + quote( "http://example.com/foo.jpg" ) +
    "&description=The+best+movie+ever.&guid=G" )

# verify the item only appear in the device.
response = call( "queue?guid=G" )
assert response["total_items"] == 1
assert response["items"][0]["title"] == "Foo"

response = call( "queue?guid=G2" )
assert response["total_items"] == 0

# fling using POST
params = {
  "url" : "http://example.com/foo.mp4",
  "title" : "Foo",
  "image" : "http://example.com/foo.jpg",
  "description" : "The best movie ever.",
  "guid" : "G2"
}
data = urllib.urlencode(params)
req = urllib2.Request( FLING_ADDR_BASE + "/fling/fling", data )
response = json.loads(urllib2.urlopen(req).read())
assert response

# get queue using POST of application/x-www-form-urlencoded body.
req = urllib2.Request( FLING_ADDR_BASE + "/fling/queue", "guid=G2" )
response = json.loads(urllib2.urlopen(req).read())
assert response["total_items"] == 1
assert response["items"][0]["title"] == "Foo"

# get queue using JSON-RPC.
call = {
    "jsonrpc" : "2.0",
    "params" : { "guid" : "G2" }, 
    "method" : "queue",
    "id" : "0"
}


req = urllib2.Request( FLING_ADDR_BASE + "/fling/", json.dumps(call) )
req.add_header( "Content-Type", "application/json-rpc" )
response = json.loads(urllib2.urlopen(req).read())
assert response["jsonrpc"] == "2.0"
assert response["result"]["total_items"] == 1
assert response["result"]["items"][0]["title"] == "Foo"

# test message sending.
# HEREDAVE

print "Passed all tests."

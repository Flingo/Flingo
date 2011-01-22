#!/usr/bin/env python

# Copyright(c) 2010. Free Stream Media Corp. Released under the terms
# of the GNU General Public License version 2.0.
#
# author: Omar Zennadi

import json
import netifaces
try:
    from netifaces import interfaces, ifaddresses
    found_netifaces = True
catch ImportError,e:
    print "WARNING! Failed to import netifaces.  You can obtain netifaces on Windows "
    print "and OSX by running:"
    print "  easy_install netifaces"
    print "Using the less reliable socket.gethostbyname to determine ip address."
    found_netifaces = False

import os
import qt4reactor
import socket
import sys
import urllib, urllib2
from PyQt4 import QtCore, QtGui
from ConfigParser import RawConfigParser

try:
   from win32com.shell import shellcon, shell
   HOMEDIR = shell.SHGetFolderPath(0, shellcon.CSIDL_MYVIDEO, 0, 0)

except ImportError: # quick semi-nasty fallback for non-windows/win32com case
   HOMEDIR = os.path.expanduser("~")

def update_config(conf_file, config={}):
   c = config
   if conf_file and os.path.isfile(conf_file):
      rv = RawConfigParser()
      rv.read(conf_file)
      if rv.has_section('fling'):
         for k,v in rv.items('fling'):
            c[k] = v
   return c

def find_config():
    config = update_config('flingo.conf')
    conf = os.getenv('FLING_CONF', default='')
    if conf:
        config = update_config(conf, config)
    return config

def get_local_ips():
   """Returns the set of known local IP addresses excluding the loopback 
      interface."""
   global found_netifaces
   ips = []
   if found_netifaces:
       ifs = [ifaddresses(i).get(netifaces.AF_INET,None) for i in interfaces()]
       ifs = [i for i in ifs if i]
       ips = []
       for i in ifs:
         ips.extend([j.get('addr',None) for j in i])
       ips = [i for i in ips if i and i != "127.0.0.1"]
   if not found_netifaces or not ips:
       ip = socket.gethostbyname(socket.gethostname())
       if ip != "127.0.0.1":
         ips.append(ip)
   return ips

config = find_config()
PORT = int(config.get('port', 8080))
FLING_ADDR_BASE = config.get('host', 'http://flingo.tv')
#FLING_ADDR_BASE = "http://dave.flingo.tv"
DEVICE_CHECK = FLING_ADDR_BASE + '/fling/has_services'
FLING_URL = FLING_ADDR_BASE + '/fling/fling'
print "DEVICE_CHECK=", DEVICE_CHECK

class FlingIcon(QtGui.QSystemTrayIcon):
   def __init__(self, parent=None):
      QtGui.QSystemTrayIcon.__init__(self, parent)

      self.menu = QtGui.QMenu(parent)
      self.menu.addAction('Fling File', self.find)
      #self.menu.addAction('Quit', self.quit)

      quit=self.menu.addAction("Quit")
      self.connect(quit,QtCore.SIGNAL('triggered()'),self.quit)

      self.file = QtGui.QFileDialog(None)
      self.file.setFileMode(QtGui.QFileDialog.ExistingFiles)
      #self.file.setFilter("Video Files (*.mp4)")
      self.file.setDirectory(HOMEDIR)
      self.file.setReadOnly(True)
      self.setContextMenu(self.menu)
      self.icon = QtGui.QIcon('flingo.png')
      self.setIcon(self.icon)

   def quit(self):
      QtGui.QApplication.quit()
      sys.exit()

   def find(self):
      response = {}
      try:
         print "searching for devices..."
         req = urllib2.Request(DEVICE_CHECK)
         response = json.loads(urllib2.urlopen(req).read())
      except Exception,e:
         print str(e)

      if response==True:
         self.fling()
      else:
         self.warning()

   def warning(self):
      QtGui.QMessageBox.warning(self.menu,"Warning","No flingable devices were found.")

   def fling(self):
      try:
         fileNames = []
         if (self.file.exec_()):
            fileNames = self.file.selectedFiles()

            for fName in fileNames:
               fileName = str(fName)
               if sys.platform=='win32':
                  fileName = fileName.replace("C:","")
               name = os.path.basename(fileName)
               params = {}
               ips = get_local_ips()
               if not ips:
                   print "Could not find ip address."
                   return

               params['url'] = 'http://' + ips[0] +':' + str(PORT) + fileName
               params['description'] = 'Desktop Fling of %s from %s' % (name, socket.gethostname())
               params['title'] = '%s via Desktop Fling' % name
               data = urllib.urlencode(params)
               req = urllib2.Request(FLING_URL, data)
               response = urllib2.urlopen(req).read()
      except Exception, e:
         print str(e)

app = QtGui.QApplication([])
qt4reactor.install()

print "Creating FlingIcon"
i = FlingIcon()
i.show()

from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File

root = "/"
if sys.platform == 'win32':
   root = "c:\\"
doc_root = File(root)

print "Starting reactor"
site = Site(doc_root)
reactor.listenTCP(PORT, site)
app.exec_()
reactor.run()

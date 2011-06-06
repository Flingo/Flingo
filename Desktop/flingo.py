#!/usr/bin/env python

# Copyright(c) 2010. Free Stream Media Corp. Released under the terms
# of the GNU General Public License version 2.0.
#
# author: Omar Zennadi, David Harrison, Andrew Mansfield

import json

try:
    from netifaces import interfaces, ifaddresses
    found_netifaces = True
except ImportError,e:
    print "WARNING! Failed to import netifaces.  You can obtain netifaces on Windows "
    print "and OSX by running:"
    print "  easy_install netifaces"
    print "Using the less reliable socket.gethostbyname to determine ip address."
    found_netifaces = False

import shutil
import os
import qt4reactor
import socket
import sys
import urllib, urllib2
from PyQt4 import QtCore, QtGui
from ConfigParser import RawConfigParser
#initialize the qt application and load the reactor for qt and twisted
app = QtGui.QApplication([])
qt4reactor.install()
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File
#get the values from the configuration file
def update_config(conf_file):
   c = {}
   if conf_file and os.path.isfile(conf_file):
      rv = RawConfigParser()
      rv.read(conf_file)
      if rv.has_section('fling'):
         for k,v in rv.items('fling'):
            if (v == 'None'):
               c[k] = None
            else:
               c[k] = v
   return c
#find the configuration file
def find_config():
    conf = os.getenv('FLING_CONF', 'flingo.conf')
    if sys.platform == 'win32':
        conf = os.environ['APPDATA'] + '\\flingo\\' + conf
        if (not os.path.exists(os.path.dirname(conf))):
            os.mkdir(os.path.dirname(conf))
        if (not os.path.isfile(conf)):
            shutil.copyfile('flingo.conf', conf)
    return conf

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

#store configuration file values, used at cleanup when exiting
def store_cfg_value(key, value=None):
   cfg_file = find_config()
   if cfg_file and os.path.isfile(cfg_file):
      cfgprsr = RawConfigParser()
      cfgprsr.read(cfg_file)
      if (cfgprsr.has_section('fling')):
         cfgprsr.set('fling', key, value)
         savecfg = open(cfg_file, 'wb')
         cfgprsr.write(savecfg)
#actions that appear as options in the menu
ACTFILE = 'Fling File'
ACTDIR  = 'Fling Directory'
ACTSETDIR  = 'Set Directory'
ACTQUIT = 'Quit'
#keys in the configuration file
NAMEKEY = 'name'
GUIDKEY = 'guid'
DIRKEY  = 'directory'
DIRCHKKEY = 'flingdir'
CACHEKEY= 'cache'
#values for the Fling Directory configuration option
CHECKED = 'Checked'
UNCHECKED = 'Unchecked'
#initialize the configuration file and get the values
config = update_config(find_config())
PORT_BASE = int(config.get('port', 8080))
FLING_ADDR_BASE = config.get('host', 'http://flingo.tv')
DEV_NAME = config.get(NAMEKEY, None)
DIR_PATH = config.get(DIRKEY, None)
FLNGDIRCHK = config.get(DIRCHKKEY, UNCHECKED)
CACHE = config.get(CACHEKEY, None)
#setup the URLs
DEVICE_CHECK = FLING_ADDR_BASE + '/fling/has_services'
print "DEVICE_CHECK=", DEVICE_CHECK
DEVICE_LOOKUP = FLING_ADDR_BASE + '/fling/lookup'
FLING_URL = FLING_ADDR_BASE + '/fling/fling'
#timer delay for polling the flung directory
TIMERDELAY = 5000
#list of (Windows) partitions to serve from
drives = []

class FlingIcon(QtGui.QSystemTrayIcon):
   def __init__(self, parent=None):
      QtGui.QSystemTrayIcon.__init__(self, parent)
      #setting self.flingdir to None so that flinging the directory doesn't happen until ready
      self.flingdir = None
      #menu widget
      self.menu = QtGui.QMenu(parent)
      #check if there's devices to fling to
      self.findAnyDevice()
      #add menu options
      self.menu.addAction(ACTFILE, self.setFlingFiles)
      self.togdir = QtGui.QAction(ACTDIR, self.menu, triggered=self.toggleFlingDir)
      self.togdir.setCheckable(True)
      self.menu.addAction(self.togdir)
      self.menu.addAction(ACTSETDIR, self.setFlingDir)
      #menu item with submenu for detected devices
      self.devs = QtGui.QAction('Set Devices', self.menu)
      self.submenu = QtGui.QMenu(self.menu)
      self.devs.setMenu(self.submenu)
      self.menu.addAction(self.devs)
      #setup an action group for detected devices so the options are exclusive selection
      self.actgrp = QtGui.QActionGroup(self.submenu)
      self.actgrp.setExclusive(True)
      #timer for flinging from directory (updates as files are added)
      self.flingtimer = QtCore.QTimer()
      QtCore.QObject.connect(self.flingtimer, QtCore.SIGNAL('timeout()'), self.servDir)
      #initialize the guid, used later for flinging to single devices
      self.guid = None
      #add detected devices to the list
      self.getDevices()
      #quit option in menu
      quit=self.menu.addAction(ACTQUIT)
      self.connect(quit,QtCore.SIGNAL('triggered()'),self.quitApp)
      #initialize what files have been flung
      self.cache = CACHE
      #initialize the fling directory for use with flung directory contents
      self.flingdir = DIR_PATH
      #start the timer if a directory was loaded from the configuration file
      if (self.flingdir != None and FLNGDIRCHK == CHECKED):
         self.togdir.trigger()
      #if the timer isn't started, make sure the Fling Directory option is unchecked
      else:
         self.togdir.setChecked(False)
      self.setContextMenu(self.menu)
      self.icon = QtGui.QIcon('flingo.png')
      self.setIcon(self.icon)
   #does some cleanup and exits the app
   def quitApp(self):
      #store fling directory checked state
      if (self.togdir.isChecked()):
         store_cfg_value(DIRCHKKEY, CHECKED)
      else:
         store_cfg_value(DIRCHKKEY, UNCHECKED)
      #remove any files from the cache that don't exist anymore
      allFiles = str(self.cache).split(',')
      self.cache = None
      for singleFile in allFiles:
         if (os.path.isfile(singleFile)):
            if (self.cache != None):
               self.cache = self.cache + ','
            else:
               self.cache = ''
            self.cache = self.cache + singleFile
      #store all the files that have been flung
      store_cfg_value(CACHEKEY, self.cache)
      #exit cleanly
      self.flingtimer.stop()
      app.quit()
      sys.exit(app.exec_())
   #determine if there are any devices that can be flung to
   def findAnyDevice(self):
      response = {}
      try:
         print "searching for devices..."
         req = urllib2.Request(DEVICE_CHECK)
         response = json.loads(urllib2.urlopen(req).read())
      except Exception,e:
         print str(e)
      #warn the user if no devices are detected
      if response!=True:
         self.noDeviceWarning()
   def noDeviceWarning(self):
      QtGui.QMessageBox.warning(self.menu,'Warning','No flingable devices were found.')
   #obtain a list of all devices that can be flung to
   def getDevices(self):
      response = {}
      try:
         req = urllib2.Request(DEVICE_LOOKUP)
         response = json.loads(urllib2.urlopen(req).read())
         if (response.get('services') != None):
            self.resps = response['services']
            #setup an action for each name, guid pair
            #add an option to select all devices, this is a dummy option to fling to all devices by default
            act = QtGui.QAction('All Devices', self.actgrp, triggered=self.selDevice)
            act.setCheckable(True)
            self.submenu.addAction(act)
            act.trigger()
            for resp in self.resps:
               if ((resp.get(NAMEKEY) != None) and (resp.get(GUIDKEY) != None)):
                  #associate each action with the action group
                  act = QtGui.QAction(str(resp[NAMEKEY]), self.actgrp, triggered=self.selDevice)
                  #make each action checkable
                  act.setCheckable(True)
                  self.submenu.addAction(act)
                  #if the device name is in the config file, set this one as checked
                  if (str(resp[NAMEKEY]) == DEV_NAME):
                     act.trigger()
      except Exception,e:
         print str(e)
   #the select device callback to switch and use the device's guid
   def selDevice(self):
      #reset the guid everytime so that default is All Devices
      self.guid = None
      sel = str(self.sender().text())
      for resp in self.resps:
         if ((resp.get(NAMEKEY) != None) and (resp.get(GUIDKEY) != None)):
            #check if a specific device is selected
            if (str(resp[NAMEKEY]) == sel):
               self.guid = str(resp[GUIDKEY])
      #store the selected value in the configuration file
      store_cfg_value(NAMEKEY, sel)
      if (self.flingdir != None):
         self.resetFlingDir()
   #toggles fling directory option on/off, if no directory is selected, automatically launches the selection dialog
   def toggleFlingDir(self):
      #if checked and no folder selected yet, launch the directory dialog selection
      if (self.togdir.isChecked() and self.flingdir == None):
         self.setFlingDir()
      #if checked and folder has been selected (serving up the directory), stop the timer
      elif (not self.togdir.isChecked()):
         self.flingtimer.stop()
      else:
      #if checked and folder is already selected, start up the timer again
         self.flingtimer.start(TIMERDELAY)
   #displays and sets the fling directory, also starts the
   def setFlingDir(self):
      try:
         fileNames = None
         self.menu.setDisabled(True)
         dir = QtGui.QFileDialog.getExistingDirectory(parent=None,
               caption='Select directory to Fling from...', directory=QtCore.QDir.currentPath())
         self.menu.setDisabled(False)
         if (dir):
            self.flingdir = dir
            #store the selected directory in the configuration file
            store_cfg_value(DIRKEY, self.flingdir)
            self.togdir.setChecked(True)
            self.resetFlingDir()
         #if the user clicks cancel on the dialog AND a directory wasn't already selected, uncheck the Fling Directory option
         elif(self.flingdir == None):
            self.togdir.setChecked(False)
      except Exception, e:
         print str(e)
   #reset the fling directory cache in the event devices or directory selection changes
   def resetFlingDir(self):
      #make sure the timer is stopped
      self.flingtimer.stop()
      #clear the cached flings
      self.cache = None
      #install timer to check for files and fling them
      if (self.togdir.isChecked()):
         self.flingtimer.start(TIMERDELAY)
   #recursively fling the files in a directory (e.g. find the files in the selected directory and subdirectories)
   def servDir(self, dir=None):
      if (dir == None):
         dir = str(self.flingdir)
      fileNames = os.listdir(dir)
      if fileNames:
         for fileName in fileNames:
            fullPath = os.path.join(dir, fileName)
            if (os.path.isfile(fullPath)):
               #if file name already flung, don't fling it
               if (str(self.cache).find(fullPath) == -1):
                  #add the file to the cache file
                  if (self.cache != None):
                     self.cache = self.cache + ','
                  else:
                     self.cache = ''
                  self.cache = self.cache + fullPath
                  #fling unflung file
                  self.fling(fullPath)
            elif (os.path.isdir(fullPath)):
               self.servDir(fullPath)
   #select and fling one or more files
   def setFlingFiles(self):
      try:
         fileNames = []
         self.menu.setDisabled(True)
         fileNames = QtGui.QFileDialog.getOpenFileNames(parent=None,
                     caption='Select files to Fling...', directory=QtCore.QDir.currentPath())
         self.menu.setDisabled(False)
         if fileNames:
            for fileName in fileNames:
               self.fling(str(fileName))
      except Exception, e:
         print str(e)

   #makes the actual "API" call to fling the file to the selected device(s)
   def fling(self, fileName):
      print "fling %s" % fileName
      try:
         port = PORT_BASE
         if sys.platform == 'win32':
            port = port + drives.index(os.path.splitdrive(fileName)[0] + '\\')
            fileName = fileName.replace(os.path.splitdrive(fileName)[0], '')
            fileName = fileName.replace('\\', '/')
         name = os.path.basename(fileName)
         #http://flingo.tv/fling/fling?[url=U | deobfuscator=D&context=C][&guid=G&title=T&description=D&image=I&preempt=P]
         params = {}
         ip = get_local_ips()[0]
         params['url'] = 'http://' + ip +':' + str(port) + fileName
         params['description'] = 'Desktop Fling of %s from %s' % (name, socket.gethostname())
         params['title'] = '%s via Desktop Fling' % name
         if (self.guid != None):
            params['guid'] = '%s' % self.guid
         data = urllib.urlencode(params)
         newurl = FLING_URL + '?' + data
         #req = urllib2.Request(FLING_URL, data)
         print "flinging url=%s" % newurl
         req = urllib2.Request(newurl)
         response = urllib2.urlopen(req).read()
      except Exception, e:
         print str(e)

print "Creating FlingIcon"
i = FlingIcon()
i.show()

if sys.platform == 'win32':
   for L in range(ord('A'), ord('Z')+1):
      drive = chr(L) + ':\\'
      if(os.path.exists(drive)):
         drives.append(drive)
else:
   drives.append('/')
port_inc = 0
for root in drives:
   doc_root = File(root)
   site = Site(doc_root)
   reactor.listenTCP(PORT_BASE+port_inc, site)
   port_inc = port_inc + 1
if sys.platform == 'darwin':
    app.exec_()
print "Starting reactor"
reactor.run()

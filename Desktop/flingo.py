#!/usr/bin/env python

# Copyright(c) 2010. Free Stream Media Corp. Released under the terms
# of the GNU General Public License version 2.0.
#
# author: Omar Zennadi

import os
import sys
import qt4reactor
import urllib, urllib2
import json
import socket
from PyQt4 import QtCore, QtGui
from ConfigParser import RawConfigParser

app = QtGui.QApplication([])
qt4reactor.install()

from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File

def update_config(conf_file, config={}):
   c = config
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

def find_config():
   config = update_config('flingo.conf')
   conf = os.getenv('FLING_CONF', default='')
   if conf:
      config = update_config(conf, config)
   return config

def store_cfg_value(key, value=None):
   cfg_file = 'flingo.conf'
   if cfg_file and os.path.isfile(cfg_file):
      cfgprsr = RawConfigParser()
      cfgprsr.read(cfg_file)
      if (cfgprsr.has_section('fling')):
         cfgprsr.set('fling', key, value)
         savecfg = open(cfg_file, 'wb')
         cfgprsr.write(savecfg)

def get_local_ip():
   addr = socket.gethostbyname(socket.gethostname())
   if addr and addr!='127.0.0.1':
      return addr
   return None

ACTFILE = 'Fling File'
ACTDIR  = 'Set Directory'
ACTQUIT = 'Quit'
NAMEKEY = 'name'
GUIDKEY = 'guid'
DIRKEY  = 'directory'
CACHEKEY= 'cache'
config = find_config()
PORT = int(config.get('port', 8080))
FLING_ADDR_BASE = config.get('host', 'http://flingo.tv')
DEV_NAME = config.get(NAMEKEY, None)
DIR_PATH = config.get(DIRKEY, None)
CACHE = config.get(CACHEKEY, None)
DEVICE_CHECK = FLING_ADDR_BASE + '/fling/has_devices'
DEVICE_LOOKUP = FLING_ADDR_BASE + '/fling/lookup'
FLING_URL = FLING_ADDR_BASE + '/fling/fling'

class FlingIcon(QtGui.QSystemTrayIcon):
   def __init__(self, parent=None):
      self.INIT_COMPLETE = False
      QtGui.QSystemTrayIcon.__init__(self, parent)

      self.cache = CACHE

      #initialize the guid, used later for flinging to single devices
      self.guid = None
      #initialize the fling directory for use with flung directory contents
      self.flingdir = DIR_PATH

      self.menu = QtGui.QMenu(parent)
      #check if there's devices to fling to
      self.find()

      #add menu options
      self.menu.addAction(ACTFILE, self.flingFile)
      self.menu.addAction(ACTDIR, self.flingDir)

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
      #add detected devices to the list
      self.getDevices()
      #quit option in menu
      quit=self.menu.addAction(ACTQUIT)
      self.connect(quit,QtCore.SIGNAL('triggered()'),self.quit)
      #start the timer if a directory was loaded from the configuration file
      if (self.flingdir != None):
         self.flingtimer.start(5000)

      self.setContextMenu(self.menu)
      self.icon = QtGui.QIcon('flingo.png')
      self.setIcon(self.icon)

      self.INIT_COMPLETE = True

   def quit(self):
      store_cfg_value(CACHEKEY, self.cache)
      app.quit()
      sys.exit(app.exec_())

   def find(self):
      response = {}
      try:
         req = urllib2.Request(DEVICE_CHECK)
         response = json.loads(urllib2.urlopen(req).read())
      except Exception,e:
         print str(e)

      if response!=True:
         self.warning()

   def warning(self):
      QtGui.QMessageBox.warning(self.menu,'Warning','No flingable devices were found.')

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
      if (self.flingdir != None and self.INIT_COMPLETE):
         self.prepDirFling()

   def flingDir(self):
      try:
         fileNames = None
         dir = QtGui.QFileDialog.getExistingDirectory(parent=None,
               caption='Select directory to Fling from...', directory=QtCore.QDir.currentPath())
         if (dir):
            self.flingdir = dir
            self.prepDirFling()
            #store the selected directory in the configuration file
            store_cfg_value(DIRKEY, self.flingdir)

      except Exception, e:
         print str(e)

   def prepDirFling(self):
      #make sure the timer is stopped
      self.flingtimer.stop()
      #clear the cached flings
      self.cache = None
      #install timer to check for files and fling them
      self.flingtimer.start(5000)

   def servDir(self, dir=None):
      if(dir == None):
         dir = str(self.flingdir)
      fileNames = os.listdir(dir)
      if fileNames:
         for fileName in fileNames:
            fullPath = os.path.join(dir, fileName)
            if (os.path.isfile(fullPath)):
               #if file name already flung, don't fling it
               if (str(self.cache).find(fullPath) == -1):
                  #add the file to the cache file
                  if(self.cache != None):
                     self.cache = self.cache + ','
                  else:
                     self.cache = ''
                  self.cache = self.cache + fullPath
                  #fling unflung file
                  self.fling(fullPath)
            elif (os.path.isdir(fullPath)):
               self.servDir(fullPath)

   def flingFile(self):
      try:
         fileNames = []
         fileNames = QtGui.QFileDialog.getOpenFileNames(parent=None,
                     caption='Select files to Fling...', directory=QtCore.QDir.currentPath())
         if fileNames:
            for fileName in fileNames:
               self.fling(str(fileName))

      except Exception, e:
         print str(e)

   def fling(self, fileName):
      try:
         if sys.platform=='win32':
            fileName = fileName.replace('C:','')
            fileName = fileName.replace('\\', '/')
         name = os.path.basename(fileName)
         #http://flingo.tv/fling/fling?[url=U | deofuscator=D&context=C][&guid=G&title=T&description=D&image=I&preempt=P]
         params = {}
         params['url'] = 'http://' + get_local_ip() +':' + str(PORT) + fileName
         params['description'] = 'Desktop Fling of %s from %s' % (name, socket.gethostname())
         params['title'] = '%s via Desktop Fling' % name
         if (self.guid != None):
            params['guid'] = '%s' % self.guid
         data = urllib.urlencode(params)
         req = urllib2.Request(FLING_URL, data)
         response = urllib2.urlopen(req).read()

      except Exception, e:
         print str(e)

i = FlingIcon()
i.show()

root = '/'
if sys.platform == 'win32':
   root = 'C:\\'
doc_root = File(root)
site = Site(doc_root)
reactor.listenTCP(PORT, site)
reactor.run()

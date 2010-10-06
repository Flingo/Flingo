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
import netifaces
import socket
from PyQt4 import QtCore, QtGui
from ConfigParser import RawConfigParser

try:
    from win32com.shell import shellcon, shell            
    HOMEDIR = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
 
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

def get_local_ip():
    addr = None
    for i in netifaces.interfaces():
        addr = netifaces.ifaddresses(i).get(2,[{}])[0].get('addr')
        if addr and addr!='127.0.0.1':
            return addr
    return None

config = find_config()    
PORT = int(config.get('port', 8080))
FLING_ADDR_BASE = config.get('host', 'http://flingo.tv')
DEVICE_CHECK = FLING_ADDR_BASE + '/fling/has_devices'
FLING_URL = FLING_ADDR_BASE + '/fling/fling'
IMAGE = config.get('image', 'http://www.flingo.tv/fling/f_icon.png')
    
class FlingIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)
        
        self.menu = QtGui.QMenu(parent)
        self.menu.addAction('Fling File', self.find)
        #self.menu.addAction('Quit', self.quit)
        
        quit=self.menu.addAction("Quit")
        self.connect(quit,QtCore.SIGNAL('triggered()'),self.quit)
        
        self.file = QtGui.QFileDialog(None)
        self.file.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.file.setFilter("Video Files (*.mp4)")
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
            
            if fileNames:
                fileName = str(fileNames[0])
                name = os.path.basename(fileName)
                params = {}
                params['url'] = 'http://' + get_local_ip() +':' + str(PORT) + fileName 
                params['image'] = IMAGE
                params['description'] = 'Desktop Fling of %s from %s' % (name, socket.gethostname())
                params['title'] = '%s via Desktop Fling' % name
                data = urllib.urlencode(params)
                req = urllib2.Request(FLING_URL, data)
                response = urllib2.urlopen(req).read()
                print response
        except Exception, e:
            print str(e)

app = QtGui.QApplication([])
qt4reactor.install()
       
i = FlingIcon()
i.show()

from twisted.internet import reactor
from twisted.web import server, resource, static
doc_root = static.File("/")
site = server.Site(doc_root)
reactor.listenTCP(PORT, site)
app.exec_()
reactor.run() 

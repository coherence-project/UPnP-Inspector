# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import time

import pygtk
pygtk.require("2.0")
import gtk

from twisted.internet import reactor

from coherence import log

class EventsWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence,max_lines=500):
        self.coherence = coherence
        self.max_lines = max_lines
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(500,400)
        self.window.set_title('Events')
        scroll_window = gtk.ScrolledWindow()
        scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.store = gtk.ListStore(str,str,str,str,str)
        self.treeview = gtk.TreeView(self.store)
        column = gtk.TreeViewColumn('Time')
        self.treeview.append_column(column)
        text_cell = gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=0)
        column = gtk.TreeViewColumn('Device')
        self.treeview.append_column(column)
        text_cell = gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=1)
        column = gtk.TreeViewColumn('Service')
        self.treeview.append_column(column)
        text_cell = gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=2)
        column = gtk.TreeViewColumn('Variable')
        self.treeview.append_column(column)
        text_cell = gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell,text=3)
        column = gtk.TreeViewColumn('Value')
        self.treeview.append_column(column)
        text_cell = gtk.CellRendererText()
        column.pack_start(text_cell, True)
        column.set_attributes(text_cell,text=4)
        scroll_window.add_with_viewport(self.treeview)
        #self.treeview.set_fixed_height_mode(True)
        self.window.add(scroll_window)
        self.coherence.connect(self.append, 'Coherence.UPnP.DeviceClient.Service.Event.processed')

    def append(self,service,event):
        if len(self.store) >= 500:
            del self.store[0]

        timestamp = time.strftime("%H:%M:%S")
        _,_,_,service_class,version = service.service_type.split(':')
        self.store.insert(0,(timestamp,service.device.friendly_name,service_class,event[0],event[1]))
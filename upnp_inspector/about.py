# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import os.path
from pkg_resources import resource_filename

import pygtk
pygtk.require("2.0")
import gtk

from upnp_inspector import __version__

class AboutWidget():

    def __init__(self):
        self.window = gtk.AboutDialog()
        self.window.set_name('UPnP Inspector')
        self.window.set_version(__version__)
        self.window.set_copyright('(c) Frank Scholz <coherence@beebits.net>')
        self.window.set_comments("""An UPnP Device and Service analyzer,
based on the Coherence DLNA/UPnP framework.
Modeled after the Intel UPnP Device Spy.""")
        self.window.set_license("""MIT\n\nIcons:
Tango Project: Creative Commons Attribution Share-Alike
David Göthberg: Public Domain""")
        self.window.set_website('http://coherence.beebits.net')
        self.window.set_authors(['Frank Scholz <fs@beebits.net>','Michael Weinrich <testsuite@michael-weinrich.de>'])
        self.window.set_artists(['Tango Desktop Project http://tango.freedesktop.org','David Göthberg: http://commons.wikimedia.org/wiki/User:Davidgothberg','Karl Vollmer: http://ampache.org'])

        logo = resource_filename(__name__, os.path.join('icons','inspector-logo.png'))
        logo = gtk.gdk.pixbuf_new_from_file(logo)
        self.window.set_logo(logo)

        self.window.show_all()

        self.window.connect('response',self.response)

    def response(self,widget,response):
        widget.destroy()
        return True
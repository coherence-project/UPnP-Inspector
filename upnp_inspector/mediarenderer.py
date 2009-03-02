# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import os

import pygtk
pygtk.require("2.0")
import gtk

if __name__ == '__main__':
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
from twisted.internet import reactor

from coherence import log
from coherence.upnp.core.utils import parse_xml, getPage

from pkg_resources import resource_filename

class MediaRendererWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self,coherence,device):
        self.coherence = coherence
        self.device = device
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.hide)
        self.window.set_default_size(400,200)
        try:
            title = 'MediaRenderer %s' % device.get_friendly_name()
        except:
            title = 'MediaRenderer'
        self.window.set_title(title)

        vbox = gtk.VBox(homogeneous=False, spacing=10)


        hbox = gtk.HBox(homogeneous=False, spacing=10)
        hbox.set_border_width(2)
        self.album_art_image = gtk.Image()
        icon = resource_filename(__name__, os.path.join('icons','blankalbum.png'))
        self.blank_icon = gtk.gdk.pixbuf_new_from_file(icon)
        self.album_art_image.set_from_pixbuf(self.blank_icon)
        hbox.pack_start(self.album_art_image,False,False,2)

        #icon_loader = gtk.gdk.PixbufLoader()
        #icon_loader.write(urllib.urlopen(str(res.data)).read())
        #icon_loader.close()

        vbox.pack_start(hbox,False,False,2)
        textbox = gtk.VBox(homogeneous=False, spacing=10)
        self.title_text = gtk.Label("<b>title</b>")
        self.title_text.set_use_markup(True)
        textbox.pack_start(self.title_text,False,False,2)
        self.album_text = gtk.Label("album")
        self.album_text.set_use_markup(True)
        textbox.pack_start(self.album_text,False,False,2)
        self.artist_text = gtk.Label("artist")
        self.artist_text.set_use_markup(True)
        textbox.pack_start(self.artist_text,False,False,2)
        hbox.pack_start(textbox,False,False,2)

        adjustment=gtk.Adjustment(value=0, lower=0, upper=240, step_incr=1,page_incr=20)#, page_size=20)
        scale = gtk.HScale(adjustment=adjustment)
        scale.set_draw_value(False)
        scale.set_sensitive(False)
        vbox.pack_start(scale,False,False,2)

        buttonbox = gtk.HBox(homogeneous=False, spacing=10)
        #button = self.make_button('media-skip-backward.png',None,sensitive=False)
        #buttonbox.pack_start(button,False,False,2)
        self.seek_backward_button = self.make_button('media-seek-backward.png',None,sensitive=False)
        buttonbox.pack_start(self.seek_backward_button,False,False,2)
        self.stop_button = self.make_button('media-playback-stop.png',callback=self.stop,sensitive=False)
        buttonbox.pack_start(self.stop_button,False,False,2)
        self.start_button = self.make_button('media-playback-start.png',callback=self.play_or_pause,sensitive=False)
        buttonbox.pack_start(self.start_button,False,False,2)
        self.seek_forward_button = self.make_button('media-seek-forward.png',None,sensitive=False)
        buttonbox.pack_start(self.seek_forward_button,False,False,2)
        #button = self.make_button('media-skip-forward.png',None,sensitive=False)
        #buttonbox.pack_start(button,False,False,2)
        vbox.pack_end(buttonbox,False,False,2)

        self.pause_button_image = gtk.Image()
        icon = resource_filename(__name__, os.path.join('icons','media-playback-pause.png'))
        icon = gtk.gdk.pixbuf_new_from_file(icon)
        self.pause_button_image.set_from_pixbuf(icon)
        self.start_button_image = self.start_button.get_image()

        self.window.add(vbox)
        self.window.show_all()

        service = self.device.get_service_by_type('AVTransport')
        service.subscribe_for_variable('AVTransportURI', callback=self.state_variable_change)
        service.subscribe_for_variable('CurrentTrackMetaData', callback=self.state_variable_change)
        service.subscribe_for_variable('TransportState', callback=self.state_variable_change)



    def make_button(self,icon,callback=None,sensitive=True):
        icon = resource_filename(__name__, os.path.join('icons',icon))
        icon = gtk.gdk.pixbuf_new_from_file(icon)
        button = gtk.Button()
        image = gtk.Image()
        image.set_from_pixbuf(icon)
        button.set_image(image)
        button.connect("clicked", lambda x: callback())
        button.set_sensitive(sensitive)
        return button

    def hide(self,w,e):
        w.hide()
        return True

    def state_variable_change(self,variable):
        print "%s %r" % (variable.name, variable.value)
        if variable.name == 'CurrentTrackMetaData':
            if variable.value != None and len(variable.value)>0:
                try:
                    from coherence.upnp.core import DIDLLite
                    elt = DIDLLite.DIDLElement.fromString(variable.value)
                    for item in elt.getItems():
                        print "now playing: %r - %r (%s/%r)" % (item.artist, item.title, item.id, item.upnp_class)
                        self.title_text.set_markup("<b>%s</b>" % item.title)
                        if item.album != None:
                            self.album_text.set_markup(item.album)
                        else:
                            self.album_text.set_markup('')
                        if item.artist != None:
                            self.artist_text.set_markup("<i>%s</i>" % item.artist)
                        else:
                            self.artist_text.set_markup("")
                        if item.albumArtURI != None:
                            def got_icon(icon):
                                icon = icon[0]
                                icon_loader = gtk.gdk.PixbufLoader()
                                icon_loader.write(icon)
                                icon_loader.close()
                                icon = icon_loader.get_pixbuf()
                                icon = icon.scale_simple(128,128,gtk.gdk.INTERP_BILINEAR)
                                self.album_art_image.set_from_pixbuf(icon)

                            d = getPage(item.albumArtURI)
                            d.addCallback(got_icon)


                except SyntaxError:
                    #print "seems we haven't got an XML string"
                    return
            else:
                self.title_text.set_markup('')
                self.album_text.set_markup('')
                self.artist_text.set_markup('')
        elif variable.name == 'TransportState':
            print variable.name, 'changed from', variable.old_value, 'to', variable.value
            if variable.value == 'PLAYING':
                self.start_button.set_image(self.pause_button_image)
            else:
                self.start_button.set_image(self.start_button_image)

        elif variable.name == 'AVTransportURI':
            print variable.name, 'changed from', variable.old_value, 'to', variable.value
            if variable.value != '':
                #self.seek_backward_button.set_sensitive(True)
                self.stop_button.set_sensitive(True)
                self.start_button.set_sensitive(True)
                #self.seek_forward_button.set_sensitive(True)
            else:
                self.seek_backward_button.set_sensitive(False)
                self.stop_button.set_sensitive(False)
                self.start_button.set_sensitive(False)
                self.seek_forward_button.set_sensitive(False)
                self.album_art_image.set_from_pixbuf(self.blank_icon)
                self.title_text.set_markup('')
                self.album_text.set_markup('')
                self.artist_text.set_markup('')


    def play_or_pause(self):
        service = self.device.get_service_by_type('AVTransport')
        variable = service.get_state_variable('TransportState', instance=0)
        print variable.value
        if variable.value != 'PLAYING':
            action = service.get_action('Play')
            d = action.call(InstanceID=0,Speed=1)
        else:
            action = service.get_action('Pause')
            d = action.call(InstanceID=0)
        d.addCallback(self.handle_result)
        d.addErrback(self.handle_error)

    def stop(self):
        service = self.device.get_service_by_type('AVTransport')
        action = service.get_action('Stop')
        d = action.call(InstanceID=0)
        d.addCallback(self.handle_result)
        d.addErrback(self.handle_error)

    def handle_error(self,e):
        print 'we have an error', e

    def handle_result(self,r):
        print "done", r

if __name__ == '__main__':

    MediaRendererWidget.hide = lambda x,y,z: reactor.stop()
    i = MediaRendererWidget(None,None)
    reactor.run()
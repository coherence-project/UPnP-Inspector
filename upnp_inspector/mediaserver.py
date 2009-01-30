# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

import os.path

import mimetypes
mimetypes.init()

import pygtk
pygtk.require("2.0")
import gtk

from twisted.internet import reactor

from coherence import log
from coherence.upnp.core.utils import parse_xml


# gtk store defines
NAME_COLUMN = 0
ID_COLUMN = 1
UPNP_CLASS_COLUMN = 2
CHILD_COUNT_COLUMN = 3
UDN_COLUMN = 4
SERVICE_COLUMN = 5
ICON_COLUMN = 6
DIDL_COLUMN = 7
TOOLTIP_ICON_COLUMN = 8

from pkg_resources import resource_filename

namespaces = {'{http://purl.org/dc/elements/1.1/}':'dc:',
              '{urn:schemas-upnp-org:metadata-1-0/upnp/}': 'upnp:',
              '{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}': 'DIDL-Lite:',
              '{urn:schemas-dlna-org:metadata-1-0}': 'dlna:',
              '{http://www.pv.com/pvns/}': 'pv:'}

class ItemDetailsWidget(object):

    def __init__(self):
        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.window.set_border_width(2)
        self.window.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.store = gtk.TreeStore(str,str)
        self.treeview = gtk.TreeView(self.store)
        self.column = gtk.TreeViewColumn()
        self.treeview.append_column(self.column)
        self.treeview.set_headers_visible(False)
        self.treeview.connect("button_press_event", self.button_action)
        text_cell = gtk.CellRendererText()
        self.column.pack_start(text_cell, False)
        self.column.set_attributes(text_cell, text=0)
        text_cell = gtk.CellRendererText()
        self.column.pack_start(text_cell, True)
        self.column.set_attributes(text_cell, text=1)
        self.window.set_size_request(400, 300)
        self.window.add(self.treeview)

    def open_url(self,url):
        import webbrowser
        webbrowser.open(url)

    def button_action(self, widget, event):
        #print "ItemDetailsWidget button_action", widget, self
        x = int(event.x)
        y = int(event.y)
        path = widget.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path,column,_,_ = path
        if event.button == 3:
            store = widget.get_model()
            iter = store.get_iter(row_path)
            menu = gtk.Menu()
            key,= store.get(iter,0)
            value,= store.get(iter,1)

            clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)

            if key in ['DIDL-Lite:res','upnp:albumArtURI']:
                item = gtk.MenuItem("copy URL")
                item.connect("activate", lambda w: clipboard.set_text(value))
                menu.append(item)
                item = gtk.MenuItem("open URL")
                item.connect("activate", lambda w: self.open_url(value))
                menu.append(item)
            else:
                item = gtk.MenuItem("copy value")
                item.connect("activate", lambda w: clipboard.set_text(value))
                menu.append(item)

            menu.show_all()
            menu.popup(None,None,None,event.button,event.time)
            return True

        return False


class TreeWidget(object):

    def __init__(self,coherence,device,
                    details_store=None,
                    cb_item_dbl_click=None,
                    cb_resource_chooser=None):
        self.details_store = details_store
        self.cb_item_dbl_click = cb_item_dbl_click
        self.cb_item_right_click = None
        self.cb_resource_chooser = cb_resource_chooser

        self.build_ui()
        self.coherence = coherence
        self.device = device
        self.mediaserver_found(device)

    def build_ui(self):
        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        icon = resource_filename(__name__, os.path.join('icons','folder.png'))
        self.folder_icon = gtk.gdk.pixbuf_new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','audio-x-generic.png'))
        self.audio_icon = gtk.gdk.pixbuf_new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','video-x-generic.png'))
        self.video_icon = gtk.gdk.pixbuf_new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons','image-x-generic.png'))
        self.image_icon = gtk.gdk.pixbuf_new_from_file(icon)

        self.store = gtk.TreeStore(str,  # 0: name or title
                                   str,  # 1: id, '0' for the device
                                   str,  # 2: upnp_class, 'root' for the device
                                   int,  # 3: child count, -1 if not available
                                   str,  # 4: device udn, '' for an item
                                   str,  # 5: service path, '' for a non container item
                                   gtk.gdk.Pixbuf,
                                   str,  # 7: DIDLLite fragment, '' for a non upnp item
                                   gtk.gdk.Pixbuf
                                )

        self.treeview = gtk.TreeView(self.store)
        self.column = gtk.TreeViewColumn('Items')
        self.treeview.append_column(self.column)

        # create a CellRenderers to render the data
        icon_cell = gtk.CellRendererPixbuf()
        text_cell = gtk.CellRendererText()

        self.column.pack_start(icon_cell, False)
        self.column.pack_start(text_cell, True)

        self.column.set_attributes(text_cell, text=0)
        self.column.add_attribute(icon_cell, "pixbuf",6)

        self.treeview.connect("row-activated", self.browse)
        self.treeview.connect("row-expanded", self.row_expanded)
        self.treeview.connect("button_press_event", self.button_action)

        #self.treeview.set_property("has-tooltip", True)
        #self.treeview.connect("query-tooltip", self.show_tooltip)

        #self.tooltip_path = None

        self.we_are_scrolling = None

        #def end_scrolling():
        #    self.we_are_scrolling = None

        #def start_scrolling(w,e):
        #    if self.we_are_scrolling != None:
        #        self.we_are_scrolling.reset(800)
        #    else:
        #        self.we_are_scrolling = reactor.callLater(800, end_scrolling)

        #self.treeview.connect('scroll-event', start_scrolling)
        self.window.set_size_request(400, 300)
        self.window.add(self.treeview)

    def show_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        if self.we_are_scrolling != None:
            return False
        ret = False
        try:
            path = self.treeview.get_dest_row_at_pos(x, y)
            iter = self.store.get_iter(path[0])
            title,object_id,upnp_class,item = self.store.get(iter,NAME_COLUMN,ID_COLUMN,UPNP_CLASS_COLUMN,DIDL_COLUMN)
            from coherence.upnp.core import DIDLLite
            if upnp_class == 'object.item.videoItem':
                self.tooltip_path = object_id
                item = DIDLLite.DIDLElement.fromString(item).getItems()[0]
                tooltip_icon, = self.store.get(iter,TOOLTIP_ICON_COLUMN)
                if tooltip_icon != None:
                    tooltip.set_icon(tooltip_icon)
                else:
                    tooltip.set_icon(self.video_icon)
                    for res in item.res:
                        protocol,network,content_format,additional_info = res.protocolInfo.split(':')
                        if(content_format == 'image/jpeg' and
                           'DLNA.ORG_PN=JPEG_TN' in additional_info.split(';')):
                            icon_loader = gtk.gdk.PixbufLoader()
                            icon_loader.write(urllib.urlopen(str(res.data)).read())
                            icon_loader.close()
                            icon = icon_loader.get_pixbuf()
                            tooltip.set_icon(icon)
                            self.store.set_value(iter, TOOLTIP_ICON_COLUMN, icon)
                            #print "got poster", icon
                            break
                title = title.replace('&','&amp;')
                try:
                    director = item.director.replace('&','&amp;')
                except AttributeError:
                    director = ""
                try:
                    description = item.description.replace('&','&amp;')
                except AttributeError:
                    description = ""
                tooltip.set_markup("<b>%s</b>\n"
                                   "<b>Director:</b> %s\n"
                                   "<b>Description:</b> %s" % (title,
                                                                director,
                                                                description))
                ret = True

        except TypeError:
            #print traceback.format_exc()
            pass
        except Exception:
            #print traceback.format_exc()
            #print "something wrong"
            pass
        return ret

    def button_action(self, widget, event):
        #print "TreeWidget button_action", widget, event, event.button
        x = int(event.x)
        y = int(event.y)
        path = widget.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path,column,_,_ = path
        if event.button == 1 and self.details_store != None:
            store = widget.get_model()
            iter = store.get_iter(row_path)
            didl,= store.get(iter,DIDL_COLUMN)
            self.details_store.clear()

            #print didl
            et = parse_xml(didl, 'utf-8')
            et = et.getroot()

            def un_namespace(text):
                for k,v in namespaces.items():
                    if text.startswith(k):
                        return text.replace(k,v)
                return text

            def append(item,row=None):
                for k,v in item.attrib.items():
                    self.details_store.append(row,(un_namespace(k),v))
                for child in item:
                    new_row=self.details_store.append(row,(un_namespace(child.tag),child.text))
                    if un_namespace(child.tag) == 'DIDL-Lite:res':
                        append(child,new_row)

            for item in et:
                append(item)


        if event.button == 3 and self.cb_item_right_click != None:
            return self.cb_item_right_click(widget, event)
        return 0

    def handle_error(self,error):
        print error

    def device_has_action(self,udn,service,action):
        try:
            self.devices[udn][service]['actions'].index(action)
            return True
        except:
            return False

    def state_variable_change( self, variable):
        #print variable.name, 'changed to', variable.value
        name = variable.name
        value = variable.value
        if name == 'ContainerUpdateIDs':
            changes = value.split(',')
            while len(changes) > 1:
                container = changes.pop(0).strip()
                update_id = changes.pop(0).strip()

                def match_func(model, iter, data):
                    column, key = data # data is a tuple containing column number, key
                    value = model.get_value(iter, column)
                    return value == key

                def search(model, iter, func, data):
                    #print "search", model, iter, data
                    while iter:
                        if func(model, iter, data):
                            return iter
                        result = search(model, model.iter_children(iter), func, data)
                        if result: return result
                        iter = model.iter_next(iter)
                    return None

                row_count = 0
                for row in self.store:
                    iter = self.store.get_iter(row_count)
                    match_iter = search(self.store, self.store.iter_children(iter),
                                    match_func, (ID_COLUMN, container))
                    if match_iter:
                        print "heureka, we have a change in ", container, ", container needs a reload"
                        path = self.store.get_path(match_iter)
                        expanded = self.treeview.row_expanded(path)
                        child = self.store.iter_children(match_iter)
                        while child:
                            self.store.remove(child)
                            child = self.store.iter_children(match_iter)
                        self.browse(self.treeview,path,None,
                                    starting_index=0,requested_count=0,force=True,expand=expanded)

                    break
                    row_count += 1

    def mediaserver_found(self,device):

        service = device.get_service_by_type('ContentDirectory')

        def reply(response):
            item = self.store.append(None)
            self.store.set_value(item, NAME_COLUMN, 'root')
            self.store.set_value(item, ID_COLUMN, '0')
            self.store.set_value(item, UPNP_CLASS_COLUMN, 'root')
            self.store.set_value(item, CHILD_COUNT_COLUMN, -1)
            self.store.set_value(item, UDN_COLUMN, device.get_usn())
            self.store.set_value(item, ICON_COLUMN, self.folder_icon)
            self.store.set_value(item, DIDL_COLUMN, response['Result'])
            self.store.set_value(item, SERVICE_COLUMN, service)
            self.store.set_value(item, TOOLTIP_ICON_COLUMN, None)
            self.store.append(item, ('...loading...','','placeholder',-1,'','',None,'',None))


        action = service.get_action('Browse')
        d = action.call(ObjectID='0',BrowseFlag='BrowseMetadata',
                                         StartingIndex=str(0),RequestedCount=str(0),
                                         Filter='*',SortCriteria='')
        d.addCallback(reply)
        d.addErrback(self.handle_error)
        service.subscribe_for_variable('ContainerUpdateIDs',callback=self.state_variable_change)
        service.subscribe_for_variable('SystemUpdateID',callback=self.state_variable_change)

    def row_expanded(self,view,iter,row_path):
        #print "row_expanded", view,iter,row_path
        child = self.store.iter_children(iter)
        if child:
            upnp_class, = self.store.get(child,UPNP_CLASS_COLUMN)
            if upnp_class == 'placeholder':
                self.browse(view,row_path,None)

    def browse(self,view,row_path,column,starting_index=0,requested_count=0,force=False,expand=False):
        #print "browse", view,row_path,column,starting_index,requested_count,force
        iter = self.store.get_iter(row_path)
        child = self.store.iter_children(iter)
        if child:
            upnp_class, = self.store.get(child,UPNP_CLASS_COLUMN)
            if upnp_class != 'placeholder':
                if force == False:
                    if view.row_expanded(row_path):
                        view.collapse_row(row_path)
                    else:
                        view.expand_row(row_path, False)
                    return

        title,object_id,upnp_class = self.store.get(iter,NAME_COLUMN,ID_COLUMN,UPNP_CLASS_COLUMN)
        if(not upnp_class.startswith('object.container') and
           not upnp_class == 'root'):
            url, = self.store.get(iter,SERVICE_COLUMN)
            if url == '':
                return
            print "request to play:", title,object_id,url
            if self.cb_item_dbl_click != None:
                self.cb_item_dbl_click(url)
            return

        def reply(r):
            #print "browse_reply - %s of %s returned" % (r['NumberReturned'],r['TotalMatches'])
            from coherence.upnp.core import DIDLLite

            child = self.store.iter_children(iter)
            if child:
                upnp_class, = self.store.get(child,UPNP_CLASS_COLUMN)
                if upnp_class == 'placeholder':
                    self.store.remove(child)

            title, = self.store.get(iter,NAME_COLUMN)
            try:
                title = title[:title.rindex('(')]
                self.store.set_value(iter,NAME_COLUMN, "%s(%d)" % (title,int(r['TotalMatches'])))
            except ValueError:
                pass
            didl = DIDLLite.DIDLElement.fromString(r['Result'])
            for item in didl.getItems():
                #print item.title, item.id, item.upnp_class
                if item.upnp_class.startswith('object.container'):
                    icon = self.folder_icon
                    service, = self.store.get(iter,SERVICE_COLUMN)
                    child_count = item.childCount
                    try:
                        title = "%s (%d)" % (item.title,item.childCount)
                    except TypeError:
                        title = "%s (n/a)" % item.title
                        child_count = -1
                else:
                    icon=None
                    service = ''

                    child_count = -1
                    title = item.title
                    if item.upnp_class.startswith('object.item.audioItem'):
                        icon = self.audio_icon
                    elif item.upnp_class.startswith('object.item.videoItem'):
                        icon = self.video_icon
                    elif item.upnp_class.startswith('object.item.imageItem'):
                        icon = self.image_icon

                stored_didl = DIDLLite.DIDLElement()
                stored_didl.addItem(item)
                new_iter = self.store.append(iter, (title,item.id,item.upnp_class,child_count,'',service,icon,stored_didl.toString(),None))
                if item.upnp_class.startswith('object.container'):
                    self.store.append(new_iter, ('...loading...','','placeholder',-1,'','',None,'',None))


            if((int(r['TotalMatches']) > 0 and force==False) or
                expand==True):
                view.expand_row(row_path, False)

            if(requested_count != int(r['NumberReturned']) and
               int(r['NumberReturned']) < (int(r['TotalMatches'])-starting_index)):
                print "seems we have been returned only a part of the result"
                print "requested %d, starting at %d" % (requested_count,starting_index)
                print "got %d out of %d" % (int(r['NumberReturned']), int(r['TotalMatches']))
                print "requesting more starting now at %d" % (starting_index+int(r['NumberReturned']))

                self.browse(view,row_path,column,
                            starting_index=starting_index+int(r['NumberReturned']),
                            force=True)

        service = self.device.get_service_by_type('ContentDirectory')
        action = service.get_action('Browse')
        d = action.call(ObjectID=object_id,BrowseFlag='BrowseDirectChildren',
                                         StartingIndex=str(starting_index),RequestedCount=str(requested_count),
                                         Filter='*',SortCriteria='')
        d.addCallback(reply)
        d.addErrback(self.handle_error)

    def destroy_object(self, row_path):
        #print "destroy_object", row_path
        iter = self.store.get_iter(row_path)
        object_id, = self.store.get(iter,ID_COLUMN)
        parent_iter = self.store.iter_parent(iter)
        service, = self.store.get(parent_iter,SERVICE_COLUMN)
        if service == '':
            return

        def reply(r):
            #print "destroy_object reply", r
            pass

        s = self.bus.get_object(BUS_NAME+'.service',service)
        s.action('destroy_object',
                 {'object_id':object_id},
                 reply_handler=reply,error_handler=self.handle_error)


class MediaServerWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self,coherence,device):
        self.coherence = coherence
        self.device = device
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.hide)
        self.window.set_default_size(400,600)
        self.window.set_title('Browse MediaServer %s' % device.get_friendly_name())
        self.item_details = ItemDetailsWidget()
        self.ui = TreeWidget(coherence,device,self.item_details.store)
        vpane = gtk.VPaned()
        vpane.add1(self.ui.window)
        vpane.add2(self.item_details.window)
        self.window.add(vpane)
        self.window.show_all()

    def hide(self,w,e):
        w.hide()
        return True
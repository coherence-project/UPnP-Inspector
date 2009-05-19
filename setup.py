# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from upnp_inspector import __version__

packages = find_packages()

setup(
    name="UPnP-Inspector",
    version=__version__,
    description="""UPnP Device and Service analyzer""",
    long_description="""UPnP-Inspector is an UPnP Device and Service analyzer,
based on the Coherence DLNA/UPnP framework.

Loosely modeled after the Intel UPnP Device Spy and the UPnP Test Tool.

Features:

 * inspect UPnP devices, services, actions and state-variables
 * invoke actions on any service
 * extract UPnP device- and service-description xml-files
 * follow and analyze events
 * interact with well-known devices
   * browse the ContentDirectory of an UPnP A/V MediaServer and inspect its containers and items
   * control an UPnP A/V MediaRenderer

This 0.2.2 - Let the Sunshine In - release includes

 * a control-window for UPnP A/V MediaRenderers
 * Drag 'n Drop functionality from the MediaServer Browse window to the MediaRenderer control
 * a 'Rediscover Devices' menu item
 * a 'Refreshing Container' context menu item and an overall refresh upon closing the MediaServer Browse window
 * support for dlna-playcontainer URIs
 * displaying all elements from a DIDLLite fragment

""",
    author="Frank Scholz",
    author_email='coherence@beebits.net',
    license = "MIT",
    packages=packages,
    scripts = ['bin/upnp-inspector'],
    url = "http://coherence.beebits.net/wiki/UPnP-Inspector",
    download_url = 'http://coherence.beebits.net/download/UPnP-Inspector-%s.tar.gz' % __version__,
    keywords=['UPnP', 'DLNA'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: X11 Applications :: Gnome',
                   'Environment :: X11 Applications :: GTK',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                ],

    package_data = {
        'upnp_inspector': ['icons/*.png'],
    },
    install_requires=[
    'Coherence >= 0.6.4',
    ]
)

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
""",
    author="Frank Scholz",
    author_email='coherence@beebits.net',
    license = "MIT",
    packages=packages,
    scripts = ['bin/upnp-inspector'],
    url = "http://coherence.beebits.net",
    download_url = 'http://coherence.beebits.net/download/UPnP-Inspector-%s.tar.gz' % __version__,
    keywords=['UPnP', 'DLNA'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: X11 Applications :: Gnome',
                   'Environment :: X11 Applications :: GTK',
                   'Environment :: Win 32 (MS Windows)',
                   'Environment :: MacOS X',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                ],

    entry_points="""
    """,

    package_data = {
        'upnp_inspector': ['icons/*.png'],
    },
    install_requires=[
    'Coherence >= 0.5.9'
    ],
)

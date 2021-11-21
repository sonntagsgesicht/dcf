# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import codecs

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

pkg = __import__('dcf')

setup(
    name=pkg.__name__,
    description=pkg.__doc__,
    version=pkg.__version__,
    author=pkg.__author__,
    author_email=pkg.__email__,
    url=pkg.__url__,
    license=pkg.__license__,
    packages=(pkg.__name__,),
    package_data={pkg.__name__: list(pkg.__data__)},
    scripts=pkg.__scripts__,
    install_requires=pkg.__dependencies__,
    dependency_links=pkg.__dependency_links__,
    long_description='\n' + codecs.open('README.rst', encoding='utf-8').read(),
    long_description_content_type='text/x-rst',
    platforms='any',
    classifiers=[
        'Development Status :: ' + pkg.__dev_status__,
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Education',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Utilities',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

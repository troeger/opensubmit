#!/usr/bin/env python
import os, sys, shutil

from setuptools import setup, find_packages
from distutils.command.install import install as _install
from distutils.command.clean import clean as _clean
from opensubmit import __version__

def clean_pycs():
    # Clean all pyc files recursively
    for root, dirs, files in os.walk('opensubmit'):
        for name in files:
            if name.endswith('.pyc'):
                fullname = os.path.join(root, name)
                print 'Removing %s' % fullname
                os.remove(fullname)

def clean_dirs():
    for path in ["OpenSubmit.egg-info","dist", "build" ]:
        shutil.rmtree(path, ignore_errors=True)

# Our overloaded 'setup.py clean' command
class clean(_clean):
    def run(self):
        _clean.run(self)
        clean_pycs()
        clean_dirs()

setup(
    name = 'OpenSubmit',
    version = __version__,
    url = 'https://github.com/troeger/opensubmit',
    license='AGPL',
    author = 'Peter Troeger',
    author_email = 'peter@troeger.eu',
    classifiers=[
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],
    install_requires=[
        'Django>=1.7',
        'django-bootstrap-form',
        'django-grappelli',
        'psutil'                            # for executor
    ],
    packages = find_packages(exclude=['opensubmit.tests']),     # Just add Python packages
    include_package_data = True,                                # Consider MANIFEST.in
    cmdclass={
        'clean': clean
    },
    entry_points={
        'console_scripts': [
            'opensubmit = opensubmit.management.production:console_script',
        ],
    }
)



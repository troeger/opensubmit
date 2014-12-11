#!/usr/bin/env python
import os, sys, shutil

from setuptools import setup, find_packages
from distutils.command.install import install as _install
from distutils.command.clean import clean as _clean
from opensubmit import __version__

#TODO: Support packaging executor, must include dependency to psutil

def check_python_version():
    version_message = 'This Django project requires Python 2.6+'

    if sys.version_info[0] < 2 or sys.version_info[0] == 2 and sys.version_info[1] < 6:
        print version_message
        exit(-1)
    elif sys.version_info[0] > 2:
        print(version_message)
        exit(-1)

check_python_version()

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

def install_config():
    config = RawConfigParser()
    try:
        config.readfp(open('/etc/opensubmit/settings.ini')) 
    except IOError:
        print "Seems like the config file /etc/opensubmit/settings.ini does not exist. I am copying the template, don't forget to edit it !"
        shutil.copyfile('settings.ini.template','/etc/opensubmit/settings.ini')

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
        'openid2rp',
        'djangorestframework>=2.4',
        'django-grappelli'
    ],    
    # "executor_api.*" must move become "opensubmit.executor_api.*" before being
    # included, otherwise we get a separate python module with a completely
    # independent name in the final installation.
    packages = find_packages(exclude=[  'executor_api', 
                                        'executor_api.migrations',
                                        'opensubmit.tests']),     # Just add Python packages
    include_package_data = True,                                  # Consider MANIFEST.in
    cmdclass={
        'clean': clean
    },
)



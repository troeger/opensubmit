#!/usr/bin/env python
import os, sys

from setuptools import setup
from distutils.command.install import install as _install
from distutils.command.clean import clean as _clean
# check FuzzEd/__init__.py for the project version number
from submit import __version__

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
    for root, dirs, files in os.walk('submit'):
        for name in files:
            if name.endswith('.pyc'):
                fullname = os.path.join(root, name)
                print 'Removing %s' % fullname
                os.remove(fullname)

def install_config():
    config = RawConfigParser()
    try:
        config.readfp(open('/etc/submit/settings.ini')) 
    except IOError:
        print "Seems like the config file /etc/submit/settings.ini does not exist. I am copying the template, don't forget to edit it !"
        shutil.copyfile('etc/settings.ini.template','/etc/submit/settings.ini')

# Our overloaded 'setup.py clean' command
class clean(_clean):
    def run(self):
        _clean.run(self)
        clean_pycs()

setup(
    name = 'Submit',
    version = __version__,
    packages = ['submit'],
    include_package_data = True,
    install_requires=[
        'django',
        'south',
        'openid2rp',
        'psycopg2',
        'django-bootstrap-form'
    ],    
    cmdclass={
        'clean': clean
    },
    data_files=[ ('etc/submit', ['submit/settings.ini.template']) ],
    maintainer = 'Peter Troeger',
    maintainer_email = 'peter.troeger@hpi.uni-potsdam.de',
	url = 'https://bitbucket.org/troeger/submit'
)

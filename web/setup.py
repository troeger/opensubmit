#!/usr/bin/env python
import os, sys, shutil

from setuptools import setup, find_packages
from distutils.command.clean import clean as _clean

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name = 'opensubmit-web',
    version = open('VERSION').read(),
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
    install_requires=required,
    packages = find_packages(exclude=['opensubmit.tests']),     # Just add Python packages
    include_package_data = True,                                # Consider MANIFEST.in
    entry_points={
        'console_scripts': [
            'opensubmit-web = opensubmit.cmdline:console_script',
        ],
    }
)



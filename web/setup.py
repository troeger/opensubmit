#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, shutil

from setuptools import setup, find_packages
from distutils.command.clean import clean as _clean

with open('requirements.txt') as f:
    required = f.read().splitlines()

def package_files(directory):
    paths = []
    excluded=['.pyc','README.md']
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            for pattern in excluded:
                if pattern in filename:
                    continue
            paths.append(os.path.join('..', path, filename))
    return paths

static = package_files('opensubmit/static')
templates = package_files('opensubmit/templates')
templatetags = package_files('opensubmit/templatetags')
data_files = static+templates+templatetags

setup(
    name = 'opensubmit-web',
    version = '0.7.15',
    url = 'https://github.com/troeger/opensubmit',
    license='AGPL',
    author = 'Peter Tröger',
    description = 'A web application for managing student assignment solutions in a university environment.',
    author_email = 'peter@troeger.eu',
    classifiers=[
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=required,
    packages = ['opensubmit', 'opensubmit.admin', 'opensubmit.management.commands', 'opensubmit.migrations', 'opensubmit.models', 'opensubmit.social', 'opensubmit.views'],     # Just add Python packages
    package_data = {'opensubmit': data_files},
    entry_points={
        'console_scripts': [
            'opensubmit-web = opensubmit.cmdline:console_script',
        ],
    }
)



#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, shutil

from setuptools import setup, find_packages
from distutils.command.clean import clean as _clean
from distutils.command.install import install

with open('requirements.txt') as f:
    required = f.read().splitlines()

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        from opensubmit import cmdline
        cmdline.check_web_db()

setup(
    name = 'opensubmit-web',
    version = open('VERSION').read()[:-1],
    url = 'https://github.com/troeger/opensubmit',
    license='AGPL',
    author = 'Peter Tröger',
    description = 'A web application for managing student assignment solutions in a university environment.',
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
    },
    cmdclass={
        'install': PostInstallCommand
    }
)



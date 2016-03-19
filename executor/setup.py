#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name = 'opensubmit-exec',
    version = open('VERSION').read(),
    url = 'https://github.com/troeger/opensubmit',
    license='AGPL',
    author = 'Peter Tröger',
    description = 'This is the executor daemon for the OpenSubmit web application.',
    author_email = 'peter@troeger.eu',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],

    install_requires=required,
    packages = find_packages(),
    include_package_data = True,
    entry_points={
        'console_scripts': [
            'opensubmit-exec = opensubmit.executor.cmdline:console_script',
        ],
    }
)



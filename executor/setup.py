#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name = 'opensubmit-exec',
    version = '0.7.16',
    url = 'https://github.com/troeger/opensubmit',
    license='AGPL',
    author = 'Peter Tröger',
    description = 'This is the executor daemon for the OpenSubmit web application.',
    author_email = 'peter@troeger.eu',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.4'
    ],

    install_requires=required,
    extras_require={'report-opencl': ["pyopencl"]},
    packages = ['opensubmitexec'],
    package_data = {'opensubmitexec': ['VERSION']},
    entry_points={
        'console_scripts': [
            'opensubmit-exec = opensubmitexec.cmdline:console_script',
        ],
    }
)



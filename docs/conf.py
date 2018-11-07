#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.abspath('../executor/'))

# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.githubpages',
    'sphinx_issues']

source_suffix = '.rst'
master_doc = 'index'
project = 'OpenSubmit'
version = '0.7.14'
release = '0.7.14'
copyright = u'2018, Peter Tröger'
author = u'Peter Tröger'
language = "en"
exclude_patterns = ['formats', 'Thumbs.db', '.DS_Store', 'modules.rst']
pygments_style = 'sphinx'
todo_include_todos = True

html_theme = "sphinx_rtd_theme"
html_favicon = '../web/opensubmit/static/images/favicon.ico'
html_logo = '../web/opensubmit/static/images/favicon-96x96.png'
html_static_path = ['css']
html_context = {
    'css_files': [
        '_static/theme_overrides.css',  # override wide tables in RTD theme
        ],
     }


napoleon_google_docstring = True
napoleon_numpy_docstring = False

issues_github_path = 'troeger/opensubmit'

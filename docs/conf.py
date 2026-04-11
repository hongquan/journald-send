# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

project = 'journald-send'
copyright = '2026, Nguyễn Hồng Quân'
author = 'Nguyễn Hồng Quân <ng.hong.quan@gmail.com>'
release = '0.1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

autodoc_default_options = {"member-order": "bysource"}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static']

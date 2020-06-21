import sys, os
import vecrec

## General

project = u'vecrec'
copyright = u'2015, Kale Kundert'
version = vecrec.__version__
release = vecrec.__version__

master_doc = 'index'
source_suffix = '.rst'
templates_path = ['templates']
exclude_patterns = ['build']
default_role = 'any'
pygments_style = 'sphinx'

## Extensions

extensions = [
        'autoclasstoc',
        'sphinx.ext.autodoc',
        'sphinx.ext.autosummary',
        'sphinx.ext.viewcode',
        'sphinx.ext.intersphinx',
]
intersphinx_mapping = { #
        'pyglet': ('http://pyglet.readthedocs.io/en/latest', None),
        'pygame': ('https://www.pygame.org/docs', None),
}
autosummary_generate = True
autodoc_default_options = {
        'exclude-members': '__dict__,__weakref__,__module__',
}

## Theme

from sphinx_rtd_theme import get_html_theme_path
html_theme = "sphinx_rtd_theme"
html_theme_path = [get_html_theme_path()]
#html_static_path = ['static']


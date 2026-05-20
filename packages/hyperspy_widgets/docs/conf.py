# -*- coding: utf-8 -*-
#
# HyperSpy Widgets documentation build configuration file.
#

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import hyperspy_widgets  # noqa: E402

# -- General configuration ------------------------------------------------

extensions = [
    "numpydoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
]

autosummary_generate = True

source_suffix = ".rst"
master_doc = "index"

project = "HyperSpy Widgets"
copyright = f"2011-{datetime.today().year}, The HyperSpy development team"

# The full version, including alpha/beta/rc tags.
release = hyperspy_widgets.__version__
# The short X.Y version.
version = ".".join(release.split(".")[:2])

exclude_patterns = ["_build"]
pygments_style = "sphinx"

# -- Options for HTML output ----------------------------------------------

html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "github_url": "https://github.com/hyperspy/hyperspy",
    "logo": {
        "text": "HyperSpy Widgets",
    },
}

# -- Intersphinx ----------------------------------------------------------

intersphinx_mapping = {
    "matplotlib": ("https://matplotlib.org/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "python": ("https://docs.python.org/3", None),
}

# -- Numpydoc -------------------------------------------------------------

numpydoc_show_class_members = False
numpydoc_xref_param_type = True

autoclass_content = "both"
autodoc_default_options = {
    "show-inheritance": True,
}

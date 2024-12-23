# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.
#
# Updated documentation of the configuration options is available at
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import datetime

from antmicro_sphinx_utils.defaults import (
    antmicro_html,
)
from antmicro_sphinx_utils.defaults import (
    extensions as default_extensions,
)
from antmicro_sphinx_utils.defaults import (
    myst_enable_extensions as default_myst_enable_extensions,
)

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.insert(0, os.path.abspath('.'))

# -- General configuration -----------------------------------------------------

# General information about the project.
project = "Caliptra RTL"
basic_filename = "caliptra-rtl-coverage-reports"
authors = "CHIPS Alliance"
copyright = f"{authors}, {datetime.now().year}"  # noqa: A001

# The short X.Y version.
version = ""
# The full version, including alpha/beta/rc tags.
release = ""

# Temporary; Remove once the clash between myst-parser and immaterial is fixed
sphinx_immaterial_override_builtin_admonitions = False

numfig = True

# If you need to add extensions just add to those lists
extensions = default_extensions
myst_enable_extensions = default_myst_enable_extensions

myst_substitutions = {}

myst_url_schemes = {
    "http": None,
    "https": None,
    "external": "{{path}}",
}

today_fmt = "%Y-%m-%d"

todo_include_todos = False

# -- Options for HTML output ---------------------------------------------------

html_theme = "sphinx_immaterial"

html_last_updated_fmt = today_fmt

html_show_sphinx = False

(html_logo, html_theme_options, html_context) = antmicro_html()


html_theme_options["palette"][0].update(
    {
        "scheme": "slate",
        "primary": "teal",
        "accent": "white",
    }
)

# # Disable toggle theme button
# html_theme_options = {
#     "palette": []
# }
html_title = project


def setup(app):
    project_name = app.config.project
    project_words = project_name.split()

    app.config.basic_filename = f"{'-'.join(project_words)}-coverage-reports"
    app.config.html_title = project_name
    myst_substitutions["project"] = project_name
    app.add_css_file("main.css")

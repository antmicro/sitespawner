# SiteSpawner (sis)

Copyright (c) 2020-2024 [Antmicro](https://www.antmicro.com)

SiteSpawner (abbreviated as `sis`) is a tool for generating coverage dashboards.

## Installation

```
pip3 install .
```

## Usage

All subcommands and accepted arguments can be listed with:

```
sis --help
```

The tool consists of 3 individual subcommands representing the three things it does (detailed below), and an `all` subcommand which performs all of them.

### Coverage data conversion

To convert `*.dat` coverage data into `*.info` files, use:

```
sis convert
```

The tool lets you pass a path to the directory containing `*.dat` files via the `--dat-dir` option.
If not specified, the current working directory will be considered.

Similarly, it lets you specify an output directory for the produced `*.info` files via the `--info-dir` option.
If not specified, the `*.info` files will be stored where their `*.dat` counterparts are.

### Coverage dashboard generation

To generate a coverage dashboard from the `*.info` files, use:

```
sis reports
```

### Webpage assembly (update)

Collect coverage dashboards (optionally documentation) and merge it into a collection of pages:

```
sis webpage --loc-github-ref-name <ref>
            --loc-github-event-name <event> --pr-number <pr_no>
```

The command expects a reference name, event name and PR number if relevant.
Those parameters dictate the localization of the generated pages in the website.

E.g. if `ref` is `main`, the coverage dashboard and documentation will be placed under `BASE_URL/main/...`.

If the pages were generated within a merge request number `<no>`, the pages will be located under `BASE_URL/dev/<no>/...`

## Package layout


* [pyproject.toml](pyproject.toml) Project setup, configuration, dependencies
* [src](src)
  * [sitespawner](src/sitespawner)
    * [common.py](src/sitespawner/common.py) Shared definitions
    * [convert_data.py](src/sitespawner/convert_data.py) `*.dat` -> `*.info` coverage files conversion
    * [gen_coverage_report.py](src/sitespawner/gen_coverage_report.py) Prepares sources & invokes `genhtml.py` in the `reports` stage
    * [generate.py](src/sitespawner/generate.py) Executed at `webpage` stage, invokes `sphinx-build` with rendered `webpage` templates
    * [genhtml.py](src/sitespawner/genhtml.py) Generates a HTML coverage report based on coverage summaries (provided by `gen_coverage_report.py`)
    * [\_\_init\_\_.py](src/sitespawner/__init__.py) Parsers & argument processing
    * [update_style.py](src/sitespawner/update_style.py) Overwrites documentation theme styles & copies assets to the final webpage directory
    * [update_webpage.py](src/sitespawner/update_webpage.py) Gathers artifacts from current execution & joins them with existing webpage (e.g. appends a new PR onto the PR list)
* [styles](styles) Custom CSS files & assets
  * [assets](styles/assets) Page assets (e.g. logos)
  * [cov.css](styles/cov.css) Styles used by the coverage dashboard
  * [main.css](styles/main.css) Styles to override documentation theme
* [template](template) Jinja2 templates for coverage reports / webpage
  * [coverage_report](template/coverage_report) HTML templates for the coverage dashboard
    * [coverage_report.html](template/coverage_report/coverage_report.html) Main coverage dashboard view
    * [main_table.html](template/coverage_report/main_table.html) Main table of the coverage dashboard, list of sources and its coverage statistics
    * [src_view.html](template/coverage_report/src_view.html) Source file view
    * [summary_table.html](template/coverage_report/summary_table.html) Coverage summary table template placed in top right corner of the coverage dashboard
  * [redirect.html](templates/redirect.html) HTML template that is used to create the main `index.html` file for the webpage
  * [webpage](templates/webpage) Final webpage templates
    * [conf.py](templates/webpage/conf.py) Sphinx configuration file
    * [coverage_dashboard.md](templates/webpage/coverage_dashboard.md) View of all coverage dashboards
    * [dev.md](templates/webpage/dev.md) Developer view (list of open PRs, branches outside of the main branch)
    * [index.md](templates/webpage/index.md) Page with references to available views (currently main & dev)
    * [main.md](templates/webpage/main.md) View on the main branch

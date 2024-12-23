# Copyright (c) 2024 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

import datetime
from collections import OrderedDict, defaultdict
from copy import deepcopy
from os.path import commonpath
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup as BS
from jinja2 import Environment, FileSystemLoader

from sitespawner.common import (
    args_on_debug_logger,
    coverage_dashboard_template_dir,
    get_logger,
    main_func_log,
)

logger = get_logger(__name__)


def gradient(percentage):
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(
            max(0, min(255, round(rgb[0]))),
            max(0, min(255, round(rgb[1]))),
            max(0, min(255, round(rgb[2])))
        )

    gradient_colors = ["#EF4444", "#F97316", "#EAB308", "#84CC16", "#16A34A"]
    colors_rgb = [hex_to_rgb(color) for color in gradient_colors]
    segment_size = 100 / (len(gradient_colors) - 1)
    segment_index = int(percentage / segment_size)
    if segment_index == len(colors_rgb) - 1:
        segment_index -= 1
    segment_percentage = (percentage - segment_index * segment_size) / segment_size
    start_color = colors_rgb[segment_index]
    end_color = colors_rgb[segment_index + 1]
    interpolated_color = tuple(
        start_color[i] + (end_color[i] - start_color[i]) * segment_percentage
        for i in range(3)
    )
    return rgb_to_hex(interpolated_color)


def get_color(value: float, total_points: int, min_value: float = 0, max_value: float = 100):
    """Given coverage level, provides the color for the visual coverage bar."""
    frac = value / total_points * 100 if total_points != 0 else 0

    return gradient(frac)


# Summary parsing # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def get_common_src_path(paths):
    """Longest common path of given `paths`."""
    return Path(commonpath([Path(x).resolve() for x in paths if Path(x).is_absolute()]))


def parse_infos(input_files: List[str]):
    for file in input_files:
        if not Path(file).is_file():
            msg = f"Input file '{file}' does not exist."
            raise FileNotFoundError(msg)

    data = defaultdict(defaultdict)

    for i in input_files:
        lines_found_sum = 0
        lines_hit_sum = 0
        module_name, _ = i.split("_")[-1].split(".")

        with open(i) as f:
            file_path = None
            lines_found = None
            lines_hit = None
            for line in f:
                if line.startswith("SF:"):
                    file_path = line[3:].strip()
                elif line.startswith("LF:"):
                    lines_found = int(line[3:])
                    lines_found_sum += lines_found
                elif line.startswith("LH:"):
                    lines_hit = int(line[3:])
                    lines_hit_sum += lines_hit
                elif line.startswith("end_of_record"):
                    data[file_path][module_name] = [lines_hit, lines_found]
                    file_path = None
                    lines_found = None
                    lines_hit = None

        data["Total:"][module_name] = [lines_hit_sum, lines_found_sum]
    return data


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# HTML components generation # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def generate_table(data, template_env, links=False):
    """Generates coverage table component."""
    cov_types = sorted(next(iter(data.items()))[1].keys(), reverse=True)
    num_tests = len(cov_types)
    raw_widths = [40, 20, 20]
    widths_arr = [str(i / num_tests) + "%" for i in raw_widths]

    name_w = 20
    cov_container_size = (100 - name_w) / num_tests
    hit_w = cov_container_size / 4
    rate_w = cov_container_size - hit_w

    template_env.globals["get_color"] = get_color
    main_table_html = template_env.get_template("main_table.html")
    # Only pass actual coverage data, leave out the summary
    # The hit rates also have to be sorted in the same way cov_types are
    cov_data = {
        k: dict(sorted(v.items(), reverse=True)) for (k, v) in data.items() if k != "Total:"
    }
    return main_table_html.render(
        cov_types=cov_types,
        width_cov_desc=sum(raw_widths) / num_tests,
        name_w=name_w,
        rate_w=rate_w,
        hit_w=hit_w,
        data=cov_data,
        widths_arr=widths_arr,
        links=links,
    )


def generate_summary(data: list, key: str, template_env: Environment, new_row=False):
    """Generates coverage summary table component that then is included next to the info header."""
    summary_html = template_env.get_template("summary_table.html")

    frac = data[0] / data[1] * 100 if data[1] != 0 else 0
    full_cov_color = get_color(data[0], data[1])
    return summary_html.render(
        new_row=new_row,
        cov_type_token=key,
        color_token=full_cov_color,
        hitrate_token=f"{frac:.1f}%",
        hit_token=str(data[0]),
        total_token=str(data[1]),
    )


def render_page(
    data,
    root_name,
    path_segments,
    out_dir,
    test_name,
    logo_src,
    logo_href,
    template_env,
    project_name,
    links=True,
):
    """Combines the final report page."""
    report_html = template_env.get_template("coverage_report.html")

    output = report_html.render(
        header_token="Full",
        project_name=project_name,
        logo_src=logo_src,
        logo_href=logo_href,
        fulltable_token=generate_table(data, template_env, links),
        root_name=root_name,
        path_segments=path_segments,
        testname_token=test_name,
        time_token=datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        **{
            f"{test}_summary_token": generate_summary(data["Total:"][test], test, template_env)
            for test in data["Total:"].keys()
        },
    )

    with open(out_dir, "w") as f:
        print(output, file=f)


def sub_src_view(
    data,
    file,
    test_name,
    root_name,
    path_segments,
    src_prefix,
    out_dir,
    html_src_dir,
    logo_src,
    logo_href,
    project_name,
    template_env,
):
    """Generate page for the source file based on the view generated by lcov's genhtml."""
    file = Path(file).resolve()

    inner_path = file.relative_to(src_prefix).parent
    html_name = f"{file.name}.gcov.html"

    main_table = None
    src_html_path = Path(html_src_dir) / inner_path / html_name

    if not src_html_path.exists():
        logger.warning(f"Not found: {src_html_path}")
        return

    with open(src_html_path) as src:
        soup = BS(src, features="html.parser")
        elem = soup.findAll("table")
        main_table = elem[len(elem) - 2]

    report_html = template_env.get_template("src_view.html")

    logger.debug(f"Generate summary for file {file.name}")

    output = report_html.render(
        header_token="Full",
        project_name=project_name,
        logo_src=logo_src,
        logo_href=logo_href,
        root_name=root_name,
        path_segments=path_segments,
        src_file_table=main_table,
        testname_token=test_name,
        time_token=datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        **{
            f"{test}_summary_token": generate_summary(data[test], test, template_env)
            for test in data.keys()
        },
    )

    with open(out_dir, "w") as f:
        print(output, file=f)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Data normalization dependent on the view # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def generate_dir_dict(data, path_to_dir):
    """Process coverage data grouped by directory/module."""
    gdict = defaultdict(lambda: defaultdict(list))
    for file, cov_data in dict(data).items():
        if file == "Total:":
            gdict[file] = deepcopy(cov_data)
            continue

        base = Path(file).resolve().parent.relative_to(path_to_dir)

        for key, d in cov_data.items():
            gdict[str(base)][key].append(d)

    return OrderedDict(sorted(gdict.items()))


def generate_file_dict(file_cov_map, base: Path, code_root_path: Path):
    """Process coverage data grouped by file."""
    gdict = defaultdict(lambda: defaultdict(list))

    for file, cov_data in dict(file_cov_map).items():
        if file == "Total:":
            continue
        if Path(file).resolve().parent.relative_to(code_root_path) == base:
            for key, data in cov_data.items():
                gdict[Path(file).name][key] = data

                if len(gdict["Total:"][key]) == 0:
                    gdict["Total:"][key] = [0, 0]

                gdict["Total:"][key][0] += data[0]
                gdict["Total:"][key][1] += data[1]

    return gdict


def unify_dict(data):
    """Adds 0-entries for tests with non reported coverage."""
    # Figure out the list of all tests:
    tests = {k for cov_data in data.values() for k in cov_data.keys()}

    # Add missing ones to the dict:
    for cov_data in data.values():
        for test in tests:
            if test not in cov_data:
                cov_data[test] = [0, 0]
    return data


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Root genhtml function # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@main_func_log(logger, "Generate HTML Coverage Report")
@args_on_debug_logger(logger)
def genhtml(
    input_files,
    src_path,
    output_dir,
    test_name,
    html_src_dir,
    project_name="Project",
    logo_src=None,
    logo_href=None,
):
    """Generates coverage dashboard from *.info files."""

    if not Path(output_dir).is_dir():
        msg = f"Output directory '{output_dir}' does not exist."
        raise FileNotFoundError(msg)

    data = parse_infos(input_files)

    # The LCOV must be ran with '--list-full-path' so that the paths to sources
    # are not 'simplified' with '...'.
    code_root_path = Path(src_path).resolve().parent

    data = unify_dict(data)
    tld = generate_dir_dict(data, code_root_path)

    template_env = Environment(loader=FileSystemLoader(coverage_dashboard_template_dir))

    for file in list(data.keys()):
        if file == "Total:":
            continue

        file_path = Path(file).resolve()
        segments = str(file_path.relative_to(code_root_path)).split("/")

        sub_src_view(
            data=data[file],
            file=file,
            test_name=test_name,
            root_name=code_root_path.name,
            path_segments=segments,
            src_prefix=Path(src_path).resolve(),
            out_dir=f"{output_dir}/index_{Path(file).name}.html",
            html_src_dir=html_src_dir,
            logo_src=logo_src,
            logo_href=logo_href,
            project_name=project_name,
            template_env=template_env,
        )

    for key in list(tld.keys()):
        if key == "Total:":
            continue
        subdata = generate_file_dict(data, Path(key), code_root_path)
        render_page(
            data=subdata,
            root_name=code_root_path.name,
            path_segments=key.split("/"),
            out_dir=f"{output_dir}/index_{key.replace('/','_')}.html",
            test_name=test_name,
            logo_src=logo_src,
            logo_href=logo_href,
            project_name=project_name,
            template_env=template_env,
        )

    for file, cov_data in tld.items():
        if file == "Total:":
            continue
        for test_type, dat in cov_data.items():
            hit, total = 0, 0
            for measurement in dat:
                hit += measurement[0]
                total += measurement[1]
            if total > 0:
                cov_data[test_type] = [hit, total]
            else:
                cov_data[test_type] = [0, 0]
    render_page(
        data=tld,
        root_name=code_root_path.name,
        path_segments=["src"],
        out_dir=f"{output_dir}/index.html",
        test_name=test_name,
        logo_src=logo_src,
        logo_href=logo_href,
        template_env=template_env,
        project_name=project_name,
        links=True,
    )

# Copyright (c) 2024 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path

from sitespawner.common import args_on_debug_logger, get_logger, main_func_log

logger = get_logger(__name__)


@args_on_debug_logger(logger=logger)
def convert_coverage_data(dat_dir, out_dir, dat_pattern="coverage*.dat"):
    """Converts *.dat coverage data files into *.info files."""
    dat_dir = Path(dat_dir)

    # Find all coverage*.dat files
    files = list(Path.glob(dat_dir, f"**/{dat_pattern}"))

    if not files:
        logger.error("No 'coverage*.dat' files were found.")
        logger.error(f"Searched directory: {dat_dir.absolute}")
        logger.error(f"{__name__} ended with errors")
        msg = "No 'coverage*.dat' data files were found."
        raise Exception(msg)

    for dat_file in files:
        info_filename = dat_file.name.replace(".dat", ".info")
        info_path = (dat_file.parent if not out_dir else Path(out_dir)) / info_filename

        try:
            subprocess.run(
                [
                    "verilator_coverage",
                    "--write-info",
                    info_path,
                    dat_file,
                ],
                check=True,
            )
            logger.debug(f"Conversion: {dat_file} -> {info_path} SUCCEEDED")
        except subprocess.CalledProcessError as e:
            msg = f"Failed to convert {dat_file}"
            raise Exception(msg) from e


@main_func_log(logger, "Convert Coverage Data: *.dat -> *.info")
def convert_data(args):
    dat_dir = args.dat_dir
    out_dir = args.info_dir

    if out_dir:
        Path(out_dir).mkdir(parents=True, exist_ok=True)

    convert_coverage_data(dat_dir, out_dir)

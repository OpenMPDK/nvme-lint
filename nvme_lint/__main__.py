#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0

Validate tables in NVMe specification
"""
import argparse
import sys

from . import scheduler
from . import utils

def main():
    """Parse command-line arguments and call relevant function"""
    parser = argparse.ArgumentParser(
        description="Validate tables in NVMe specification",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "file", help="The pdf file containing the tables to validate",
    )

    parser.add_argument(
        "-l", "--log",
        help="The logging level. Possible values in order of severity: \
        DEBUG, INFO, WARNING, ERROR, CRITICAL",
        default="INFO",
        required=False
    )

    parser.add_argument(
        "-i", "--ignore",
        help="A .txt file containing figure numbers to ignore, each number should go on a separate line. \
        This file will be ignored if a target is specified",
        required=False
    )

    parser.add_argument(
        "-t", "--target",
        help="A .txt file containing figure numbers to validate, each number should go on a separate line. \
        If this file is specified only the figure numbers included will be validated",
        required=False
    )

    parser.add_argument(
        "-y", "--yaml",
        action="store_true",
        help="If this flag is set, the content of the tables will be written to 'output.yaml' \
        NOTE: If you have a file called `output.yaml` in the directory you call `nvme-lint` from, \
        it will be overwritten",
        required=False
    )

    args = parser.parse_args()

    utils.config_log_level(args.log)

    if args.ignore:
        args.ignore = utils.expand_path(args.ignore)
    else:
        args.ignore = ""

    if args.target:
        args.target = utils.expand_path(args.target)
    else:
        args.target = ""

    scheduler.main(utils.expand_path(args.file), args.ignore, args.target, args.yaml)


if __name__ == "__main__":
    sys.exit(main())

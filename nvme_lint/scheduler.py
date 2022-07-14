#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0

Schedule multiple instances of the parser and collect results
"""
import concurrent.futures
from itertools import repeat
import traceback

from . import captions
from . import extractor
from . import parser
from . import transformer
from . import utils

import camelot
import yaml

logger = utils.get_logger("Scheduler")


def schedule(file_path, ignore_path, target_path):
    """Assign each page to a different process and collect results in dict"""
    page_height = get_page_height(file_path)
    with concurrent.futures.ProcessPoolExecutor(10) as executor:
        pages = {}
        for page in executor.map(parse, list(captions.main(file_path, ignore_path, target_path)), repeat(file_path), repeat(page_height)):
            pages.update(page)
        return pages


def parse(page_number_to_content, file_path, page_height):
    """Pass args to the parser"""
    page_number, tables = extractor.main(file_path, page_height, *page_number_to_content)
    if tables:
        try:
            return parser.main(page_number, tables)
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error(f"Error on page {page_number}: {type(e).__name__} {e}")
            return {}
    else:
        return {}


def get_page_height(file_path):
    """Get the height of the page according to Camelot"""
    _, dim = camelot.utils.get_page_layout(file_path)
    return dim[1]


def write_to_yaml(output):
    """Write content to yaml"""
    with open("output.yaml", "w") as file:
        yaml.dump(output, file, default_flow_style=None)


def transform(pages):
    return transformer.main(pages)


def main(file_path, ignore_path, target_path, yaml):
    """Entry point"""
    try:
        pages = schedule(file_path, ignore_path, target_path)
        pages = transform(pages)
        if yaml:
            write_to_yaml(pages)
    except FileNotFoundError as e:
        logger.critical(f"File not found: {e}")
        return 1

    return 0

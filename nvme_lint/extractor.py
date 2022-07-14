#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0

Extract raw content from NVMe specification tables
"""

from . import utils
import camelot


def extract_tables(file_path, page_height, page_number, content):
    """Extract the tables on given page"""
    tables_on_page = camelot.read_pdf(file_path, page_number, line_scale=35)
    tables = {}
    for caption, table in match_caption_to_table(tables_on_page, page_height, content):
        if caption != "skip":
            tables.update({caption: table})
    return page_number, tables


def match_caption_to_table(tables, page_height, content):
    for table in tables:
        table_y = table.cells[0][0].lt[1]/page_height
        caption_differences = [calc_difference(caption_y, table_y, content["height"])
                               for caption_y in content["top_coordinates"]]
        minimum_index = caption_differences.index(min(caption_differences))
        yield content["captions"][minimum_index], table


def calc_difference(caption_y, table_y, content_height):
    return abs((1 - caption_y / content_height) - table_y)


def main(file_path, page_height, page_number, content):
    """Entry point"""
    global logger
    logger = utils.get_logger(f"Extractor.Page {page_number}")
    try:
        return extract_tables(file_path, page_height, page_number, content)
    except FileNotFoundError as e:
        logger.critical(e)
        return page_number, {}

#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0

Parse content of NVMe specification table
"""

import re
from . import utils


def parse_page(page_number, tables):
    """Read tables, remove first row of each and concatenate"""
    page = {page_number: {}}
    for caption, table in tables.items():
        page[page_number].update(parse_table(caption, table))

    logger.debug("Page successfully parsed")
    return page


def parse_table(caption, table):
    """Parse headings, remove notes and headings from table"""
    table = table.df
    headings = parse_headings(table.head(1).to_numpy()[0])
    # Check if the first word in the first row from the bottom is NOTES
    first_word_of_last_row = table.tail(1).to_numpy()[0][0].split(":")[0]
    if "NOTE" in first_word_of_last_row or "Note" in first_word_of_last_row:
        if first_word_of_last_row != "NOTES":
            logger.warning(f"'{first_word_of_last_row}' should be 'NOTES'")
        table = table.iloc[:-1, :]
    if content := parse_content(headings, table.drop(0).reset_index(drop=True)):
        return {caption: content}
    else:
        return {}


def parse_headings(row):
    """Parse headings from row of table given as a dataframe"""
    headings = [h.lower().replace("\n", "")
                for h in row if h not in [None, ""]]

    # rename bit to bits - ideally this should never happen
    for i, heading in enumerate(headings):
        if heading == "bit":
            headings[i] = "bits"
            logger.warning(f"'{heading}' instead of 'bits'")

    # rename byte to bytes - ideally this should never happen
    for i, heading in enumerate(headings):
        if heading == "byte":
            headings[i] = "bytes"
            logger.warning(f"'{heading}' instead of 'bytes'")

    # clean-up headings containing value - this is for practical reasons
    for i, heading in enumerate(headings):
        if heading != "value" and "value" in heading:
            headings[i] = "value"
            logger.debug(f"Normalized '{heading}' to 'value'")

    return headings


def parse_content(headings, table):
    """Parse content from table"""
    output = []
    subheadings = None
    for row in table.itertuples(index=False, name=None):
        if all(value == "" for value in row):
            # skip empty rows
            continue

        elif all(value == "" for value in row[:len(headings)]):
            # Parse nested tables
            if subheadings is None:
                subheadings = parse_headings(row)
            elif subheadings:
                if output:
                    output[-1]["children"].append(
                        parse_row(row, subheadings, len(headings))
                    )
            else:
                if output:
                    output[-1]["children"].append(
                        parse_row(row, headings, len(headings))
                    )
        else:
            output.append(parse_row(row, headings, 0))

            # reset subheadings
            subheadings = None
    return output


def parse_row(row, headings, start_index):
    """Parse content from row given as a tuple"""
    content = {"children": []}

    name_brief_verbose_regex = re.compile(
        r"(?P<brief>.+?)\((?P<name>.+?)\):(?P<verbose>.+)"
    )
    brief_verbose_regex = re.compile(r"(?P<brief>.+?):(?P<verbose>.+)")
    value_range = re.compile(r"\d+ to \d+")
    hexadecimal_value = re.compile(r"\d+h")

    for i, heading in enumerate(headings):
        current_position = row[start_index + i]
        if heading in ["bits", "bytes"]:
            try:
                bs = [int(b) for b in current_position.split(":")]
                if len(bs) == 2 and bs[0] < bs[1]:
                    logger.warning(f"{heading} range is in wrong order: {current_position}")
                    bs.sort(reverse=True)
                content[heading] = bs
            except ValueError as e:
                if value_range.match(current_position):
                    logger.warning(f"{heading} range is of the wrong format: {current_position}")
                    # Convert 'a to b' to 'b to a'
                    content[heading] = sorted([int(b) for b in current_position.split("to")], reverse=True)
                elif hexadecimal_value.match(current_position):
                    logger.warning(f"{heading} value is of the wrong type: {current_position}")
                elif not current_position:
                    # The error from casting an empty string is only relevant for debugging
                    logger.debug(f"{heading} value is an empty string")
                else:
                    logger.debug(e)
                    content[heading] = current_position.split(":")

        elif match := name_brief_verbose_regex.match(
                current_position.replace("\n", "")):
            content["name"] = match.group("name").strip().lower()
            content["brief"] = match.group("brief").strip()
            content["verbose"] = match.group("verbose").strip()

        elif match := brief_verbose_regex.match(
                current_position.replace("\n", "")):
            content["brief"] = match.group("brief").strip()
            content["verbose"] = match.group("verbose").strip()

        else:
            content[heading] = current_position

    return content


def main(page_number, tables):
    """Entry point"""
    global logger
    logger = utils.get_logger(f"Parser.Page {page_number}")
    return parse_page(page_number, tables)

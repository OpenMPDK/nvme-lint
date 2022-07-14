#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0

Extract captions from all figures in the NVMe specification
"""
from itertools import chain
import re
import subprocess

from . import utils

import xml.etree.ElementTree as ET

logger = utils.get_logger("Captions")


def find_figures(file_path, ignore_path, target_path):
    """Find figures on every page"""
    xml = subprocess.run(["pdftohtml", "-xml", "-stdout", "-i", file_path],
                         stdout=subprocess.PIPE, text=True)
    tree = ET.fromstring(xml.stdout)
    pages = tree.findall(".//page")
    ignore = get_ignore(ignore_path)
    target = get_target(target_path)
    current_figure = 1
    for page in pages:
        if captions := extract_captions(page):
            captions_text = list(get_text(captions))
            current_figure, captions_to_skip = check_figure_number(
                captions_text, current_figure, ignore, target)

            # skip entire page if all captions should be skipped
            if len(captions) != len(captions_to_skip):
                for caption_number in captions_to_skip:
                    captions_text[caption_number] = "skip"
                yield page.get("number"), {"height": int(page.get("height")),
                                           "captions": captions_text,
                                           "top_coordinates": [get_top(caption)
                                                               for caption in captions]
                                           }


def check_figure_number(captions, current_figure, ignores, targets):
    """Check that no captions are missing and skip irrelevant figures"""
    regex = re.compile(r"Figure (?P<number>\d+): .+")
    captions_to_skip = []
    for i, caption in enumerate(captions):
        if match := regex.match(caption):
            if int(match.group("number")) == current_figure + 1:
                current_figure += 1
            elif int(match.group("number")) != current_figure:
                for missing in range(1, int(match.group("number")) - current_figure):
                    logger.warning(f"Encountered a problem with the caption to Figure {current_figure + missing}")
                    current_figure = int(match.group("number"))

            if targets and int(match.group("number")) not in targets:
                # Extract only the targets specified in targets.txt, if it contains anything
                captions_to_skip.append(i)
            elif int(match.group("number")) in ignores:
                # skip tables from the ignore file
                captions_to_skip.append(i)
        else:
            # skip tables with an invalid caption
            captions_to_skip.append(i)
    return current_figure, captions_to_skip


def get_ignore(ignore_path):
    """Read lines from file specifying which figures to ignore"""
    if ignore_path:
        try:
            with open(ignore_path) as file:
                return [int(line) for line in file.readlines()]
        except FileNotFoundError as e:
            logger.error("Ignore file not found: ", e)
    return []


def get_target(target_path):
    """Read lines from file specifying which figures to extract"""
    if target_path:
        try:
            with open(target_path) as file:
                return [int(line) for line in file.readlines()]
        except FileNotFoundError as e:
            logger.error("Target file not found: ", e)
    return []


def extract_captions(page):
    """Extract captions from page"""
    elements = page.findall(".//text[b]")
    return list(sort_by_top(
                    remove_non_figure_text(
                        concat_dashed_elements(
                            remove_empty_elements(
                                flatten_bold_elements(elements))))))


def flatten_bold_elements(elements):
    """Make parent include text from a bold child"""
    for element in elements:
        child = element.find(".//b")
        element.text = child.text
        yield element


def remove_empty_elements(elements):
    """Remove any elements with no text"""
    for element in elements:
        if element.text.strip():
            yield element


def concat_dashed_elements(elements):
    """Remove false linebreaks caused by a dash"""
    skip = False
    for first, second in utils.pairwise(chain(elements, [None])):
        if skip:
            skip = False
        elif second is None:
            yield first
        elif is_same_line(first, second):
            first.text += second.text
            skip = True
            yield first
        else:
            yield first


def is_same_line(first, second):
    """Check if 2 elements is on the same line"""
    first_right = int(first.get("left")) + int(first.get("width"))
    first_top = int(first.get("top"))
    second_left = int(second.get("left"))
    second_top = int(second.get("top"))
    return 0 <= abs(first_top - second_top) <= 3 and 0 <= second_left - first_right <= 3


def remove_non_figure_text(elements):
    """Remove any elements that doesn't include 'Figure'"""
    for element in elements:
        if element.text.startswith("Figure"):
            yield element


def get_top(element):
    """Get top coordinate from element"""
    return int(element.get("top"))


def sort_by_top(elements):
    """Sort elements by their top coordinate"""
    return sorted(elements, key=get_top)


def get_text(elements):
    """Yield only the text of each element and remove whitespace at the end"""
    for element in elements:
        yield element.text.strip()


def main(file_path, ignore_path, target_path):
    """Entry point"""
    try:
        return find_figures(file_path, ignore_path, target_path)
    except FileNotFoundError as e:
        logger.critical(f"File not found {e}")
        return {}

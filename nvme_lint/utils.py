#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0

Utilities for nvme-lint
"""
import logging
from pathlib import Path
from itertools import tee
import os

log_level = logging.INFO


def expand_path(path):
    """Expands variables from the given path and turns it into absolute path"""

    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def get_logger(name):
    """Return a logger with the given name and correct format"""
    logger = logging.getLogger(name)
    logger.setLevel(level=log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path())
    file_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(file_handler)
    return logger


def log_path():
    if "XDG_DATA_HOME" in os.environ:
        target = expand_path("$XDG_DATA_HOME")
    else:
        target = expand_path("~/.local/share")

    log_directory = Path(target) / "nvme-lint"
    if not log_directory.exists():
        log_directory.mkdir(parents=True)

    return log_directory / "nvme-lint.log"


def config_log_level(user_level):
    """Configure the logging level based on user input"""
    global log_level
    level = getattr(logging, user_level.upper())
    if not isinstance(level, int):
        logging.warning("Logging level unrecognized, defaulting to INFO")
    else:
        log_level = level


# from https://docs.python.org/3.8/library/itertools.html
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

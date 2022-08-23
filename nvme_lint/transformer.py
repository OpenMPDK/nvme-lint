#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0

Transform and clean up tables
"""
import math
import re
import traceback
from . import utils

logger = utils.get_logger("Transformer")

# Regex to find hexadecimal numbers and ranges
hex_value = re.compile(r"^[0-9A-F]+h$")
hex_range = re.compile(r"^[0-9A-F]+h to [0-9A-F]+h$")


class Table(list):
    """Class to facilitate chaining of transformations"""

    def __init__(self, title, rows):
        self.title = title
        self.rows = rows
        self.number = 0
        self.group = ""
        self.spec_type = ""
        self.c_type = ""
        self.headings = self.create_headings()

    def create_headings(self):
        """Create headings from first row.
        If first row is reserved create headings from second row"""
        if "description" in self.rows[0] and self.rows[0]["description"] == "Reserved":
            return list(self.rows[1].keys())
        else:
            return list(self.rows[0].keys())

    def remove_empty_children(self):
        """Remove key 'children' if the list is empty"""
        for row in self.rows:
            if not row["children"]:
                del row["children"]

        # Remove heading if no children are present in the entire table
        if all("children" not in row.keys() for row in self.rows):
            self.headings.remove("children")

    def enforce_headings(self):
        """Remove rows that do not align with the headings,
        e.g. if 'bits' are in the headings, remove rows that do not have 'bits'"""
        if "bits" in self.headings:
            self.rows = [row for row in self.rows if row.get("bits")]
        elif "bytes" in self.headings:
            self.rows = [row for row in self.rows if row.get("bytes")]

    def generate_name(self):
        """Generate a value for the 'name' key if it doesn't exist"""
        for row in self.rows:
            if "name" not in row:
                if row.get("description") == "Reserved":
                    row["name"] = "rsvd"
                elif "brief" in row:
                    if "bits" or "bytes" in row:
                        logger.debug(f"{self.title}: field {row['brief']} is missing name")
                    row["name"] = row["brief"].lower().replace(" ", "_")
                else:
                    name = row["definition"] if "definition" in row else row.get("description", "skip")
                    row["name"] = name.lower().replace(" ", "_")

    def process_title(self):
        """Convert the title to number, group and title or number and title"""
        number_group_title = re.compile(r"Figure (?P<number>\d+): (?P<group>.+) \u2013 (?P<title>.+)")
        number_title = re.compile(r"Figure (?P<number>\d+): (?P<title>.+)")
        if match := number_group_title.match(self.title):
            self.number = int(match.group("number"))
            self.group = match.group("group").lower().replace(" ", "_")
            self.title = match.group("title").lower()
        elif match := number_title.match(self.title):
            self.number = int(match.group("number"))
            self.title = match.group("title").lower()

    def determine_c_type(self):
        """Determine whether group is an enum or struct"""
        if [heading for heading in self.headings if "hex-" in heading]:
            self.c_type = "enum"
        else:
            self.c_type = "struct"

    def determine_spec_type(self):
        """Determine whether group is a command"""
        if "command dword" in self.title:
            self.spec_type = "command"
        elif "data pointer" in self.title:
            self.spec_type = "data pointer"

    def clean_bits_and_bytes(self):
        """Clean up bytes and bits and remove rows without an integer value"""
        heading = ""
        if "bits" in self.headings:
            heading = "bits"
        elif "bytes" in self.headings:
            heading = "bytes"

        if heading:
            self.check_order()
            self.check_for_holes(heading)
            self.check_overlap(heading)
            self.calculate_bits_and_bytes(heading)
            self.check_sum(heading)
            self.rows = [row for row in self.rows
                         if isinstance(row[heading], int)]

    def calculate_bits_and_bytes(self, heading):
        """Convert the bits and bytes to a single number instead of a range"""
        for row in self.rows:
            if not all(isinstance(value, int) for value in row[heading]):
                logger.debug(f"{self.title} contains non integer values in {heading} column")
            elif len(row[heading]) == 1:
                row[heading] = 1
            else:
                row[heading] = row[heading][0] - row[heading][1] + 1

    def check_order(self):
        """Check that bits go from high to low and hex values and bytes from low to high"""
        if "bits" in self.headings and len(self.rows) > 1 and sorted(self.rows, key=lambda row: row["bits"][0], reverse=True) != self.rows:
            logger.warning(f"{self.title}: bits are in wrong order")
            self.rows = sorted(self.rows, key=lambda row: row["bits"][0], reverse=True)

        elif "bytes" in self.headings and len(self.rows) > 1 and sorted(self.rows, key=lambda row: row["bytes"][0]) != self.rows:
            logger.warning(f"{self.title}: bytes are in wrong order")
            self.rows = sorted(self.rows, key=lambda row: row["bytes"][0])

    def check_sum(self, heading):
        """Check that the sum of bits and bytes is a power of 2"""
        row_sum = sum(row[heading] for row in self.rows)
        if not math.log(row_sum, 2).is_integer():
            logger.warning(f"{self.title}: sum of {heading} is not a power of 2")

    def check_overlap(self, heading):
        """Check that no bit or byte is present twice"""
        sequence = []
        for row in self.rows:
            if len(row[heading]) == 1:
                sequence.append(row[heading][0])
            else:
                sequence.extend(range(row[heading][1], row[heading][0]+1))
        if len(sequence) != len(set(sequence)):
            logger.warning(f"{self.title}: overlap of {heading}")

    def check_for_holes(self, heading):
        """Check that there are no holes in the bits and bytes"""
        sequence = []
        for row in self.rows:
            if len(row[heading]) == 1:
                sequence.append(row[heading][0])
            else:
                sequence.extend(range(row[heading][1], row[heading][0]+1))
        sequence.sort()
        if any(abs(j - i) > 1 for i, j in zip(sequence[:-1], sequence[1:])):
            logger.warning(f"{self.title}: hole in {heading}")

    def reverse_bits_rows(self):
        """Reverse the order of rows if the table contains bits"""
        if "bits" in self.headings:
            self.rows = list(reversed(self.rows))

    def clean_hex(self):
        """Clean up hex values and remove non hex values from hex columns"""
        self.detect_hex_columns()
        for heading in [heading for heading in self.headings if "hex-" in heading]:
            self.rows = [row for row in self.rows
                         if hex_value.match(row[heading])
                         or hex_range.match(row[heading])]
            self.remove_hex_ranges(heading)
            self.change_hex_format(heading)

    def detect_hex_columns(self):
        """Change headings of columns with hex values to 'hex'"""
        headings_to_change = set()
        for row in self.rows:
            for i, heading in enumerate(self.headings):
                try:
                    if hex_value.match(row.get(heading)) or hex_range.match(row.get(heading)):
                        headings_to_change.add(i)
                except TypeError:
                    continue

        for index in headings_to_change:
            old_heading = self.headings[index]
            for row in self.rows:
                row[f"hex-{old_heading}"] = row[old_heading]
                del row[old_heading]

            self.headings[index] = f"hex-{old_heading}"

    def remove_hex_ranges(self, heading):
        """Remove hex ranges as they're"""
        self.rows = [row for row in self.rows if not hex_range.match(row[heading])]

    def change_hex_format(self, heading):
        """Change hex format from {n}h to 0x{n}"""
        for row in self.rows:
            row[heading] = "0x" + row[heading].strip("h")

    def process_children(self):
        """Apply relevant functions to child table"""
        for row in self.rows:
            if "children" in row:
                # This is for the error messages to make sense
                child_title = f"Figure {self.number}:children"

                table = Table(child_title, row["children"])
                method_names = ["remove_empty_children",
                                "enforce_headings",
                                "clean_bits_and_bytes",
                                "clean_hex",
                                "reverse_bits_rows"]

                for name in method_names:
                    try:
                        getattr(table, name)()
                    except Exception as e:
                        logger.debug(traceback.format_exc())
                        logger.debug(f"{child_title} Method {name} failed: {type(e).__name__} {e}")
                row["children"] = table.rows


def transform(tables):
    """Apply tranformations to tables"""
    groups = {}
    for title, rows in tables.items():
        table = Table(title, rows)
        method_names = ["remove_empty_children",
                        "enforce_headings",
                        "clean_bits_and_bytes",
                        "clean_hex",
                        "reverse_bits_rows",
                        "generate_name",
                        "process_title",
                        "determine_spec_type",
                        "determine_c_type",
                        "process_children"]

        for name in method_names:
            try:
                getattr(table, name)()
            except Exception as e:
                logger.debug(traceback.format_exc())
                logger.debug(f"{title}: Method {name} failed: {type(e).__name__} {e}")

        transformed_table = {"title": table.title,
                             "number": table.number,
                             "rows": table.rows,
                             "spec_type": table.spec_type,
                             "c_type": table.c_type,
                             "headings": table.headings}

        if table.group in groups:
            groups[table.group].append(transformed_table)
        else:
            groups[table.group] = [transformed_table]
    return groups


def flatten_pages(pages):
    """Place tables from each page into the same dict.
    Concat tables spanning multiple pages"""
    tables = {}
    for table in pages.values():
        for k, v in table.items():
            if k in tables:
                tables[k] += v
            else:
                tables[k] = v
    return tables


def collect_types(groups):
    """Collect types of the group and add them"""
    transformed = {}
    for group_name, tables in groups.items():
        c_type = ""
        spec_type = ""

        # Collect spec type
        if any("command dword" in table["title"] for table in tables):
            spec_type = "command"

        # Collect c type
        if all(table["c_type"] == "enum" for table in tables):
            c_type = "enum"
        elif all(table["c_type"] == "struct" for table in tables):
            c_type = "struct"
        else:
            c_type = "skip"
            logger.debug(f"{group_name} is a mix of enums and structs and will be skipped")

        for table in tables:
            del table["c_type"]
            del table["spec_type"]

        transformed.update({group_name: {"tables": tables,
                                         "spec_type": spec_type,
                                         "c_type": c_type}})

    return transformed


def process_commands(groups):
    """Check for missing commands and make sure bits are correct"""
    for group_name, content in groups.items():
        if content["spec_type"] == "command":
            regex = re.compile(r"dword (?P<number>\d+)")
            commands = gen_empty_commands()

            for table in content["tables"]:
                matches = re.findall(regex, table["title"])
                if len(matches) == 2:
                    if 64 == sum(row["bits"] for row in table["rows"]):
                        table.update({"type": 64})
                        commands[int(matches[0])] = table
                        # If 2 commands present in 1 table
                        # Skip the table at the index of the second command
                        commands[int(matches[1])]["title"] = "skip"
                    else:
                        logger.warning(f"Figure {table['number']}: {table['title']} bits doesn't sum up to 64")
                elif len(matches) == 1:
                    if 32 == sum(row["bits"] for row in table["rows"]):
                        table.update({"type": 32})
                        commands[int(matches[0])] = table
                    else:
                        logger.warning(f"Figure {table['number']}: {table['title']} bits doesn't sum up to 32")
            content["tables"] = commands


def gen_empty_commands():
    """Generate a list of empty commands"""
    commands = []
    for i in range(0, 16):
        commands.append({
            "headings": ["bits", "name"],
            "number": -1,
            "rows": [{"bits": 32, "name": f"cdw{i}"}],
            "title": "",
            "type": 32
            })
    return commands


def main(pages):
    """Entry point"""
    tables = flatten_pages(pages)
    groups = transform(tables)
    groups = collect_types(groups)
    process_commands(groups)
    return groups

#!/usr/bin/env python3
"""
Copyright (c) 2022 Samsung Electronics Co., Ltd
SPDX-License-Identifier: GPLv2-or-later or Apache-2.0
"""
from copy import deepcopy
import pytest
from nvme_lint import transformer


bits_table = transformer.Table("test table", [
        {"bits": [3,0]},
        {"bits": [6,4]},
        {"bits": [31,8]},
        {"bits": [31,16]}
    ])

bytes_table = transformer.Table("test table", [
        {"bytes": [31,16]},
        {"bytes": [31,8]},
        {"bytes": [6,4]},
        {"bytes": [3,0]},
    ])


half_bits_table = transformer.Table("test table", [
        {"bits": [14,11]},
        {"bits": [10]},
        {"bits": [9]},
        {"bits": [8]},
    ])

half_bytes_table = transformer.Table("test table", [
        {"bytes": [8]},
        {"bytes": [9]},
        {"bytes": [10]},
        {"bytes": [14,11]},
    ])

unordered_bits_table = transformer.Table("test table", [
        {"bits": [15,8]},
        {"bits": [31,16]},
        {"bits": [7,4]},
        {"bits": [3,0]},
    ])

unordered_bytes_table = transformer.Table("test table", [
        {"bytes": [3,0]},
        {"bytes": [15,8]},
        {"bytes": [7,4]},
        {"bytes": [31,16]},
    ])

healthy_bits_table = transformer.Table("test table", [
        {"bits": [31,16]},
        {"bits": [15,8]},
        {"bits": [7,4]},
        {"bits": [3,0]},
    ])

healthy_bytes_table = transformer.Table("test table", [
        {"bytes": [3,0]},
        {"bytes": [7,4]},
        {"bytes": [15,8]},
        {"bytes": [31,16]},
    ])


@pytest.mark.parametrize("table, result, type", [(deepcopy(bits_table), [4, 3, 24, 16], "bits"),
                                                 (deepcopy(healthy_bits_table), [16, 8, 4, 4], "bits"),
                                                 (deepcopy(half_bits_table), [4, 1, 1, 1], "bits"),
                                                 (deepcopy(bytes_table), [16, 24, 3, 4], "bytes"),
                                                 (deepcopy(healthy_bytes_table), [4, 4, 8, 16], "bytes"),
                                                 (deepcopy(half_bytes_table), [1, 1, 1, 4], "bytes")])
def test_calculate_bits(table, result, type, caplog):
    table.calculate_bits_and_bytes(type)
    assert table.rows[0][type] == result[0]
    assert table.rows[1][type] == result[1]
    assert table.rows[2][type] == result[2]
    assert table.rows[3][type] == result[3]


@pytest.mark.parametrize("table, result", [(deepcopy(bits_table), "bits are in wrong order"),
                                           (deepcopy(unordered_bits_table), "bits are in wrong order"),
                                           (deepcopy(healthy_bits_table), ""),
                                           (deepcopy(half_bits_table), ""),
                                           (deepcopy(bytes_table), "bytes are in wrong order"),
                                           (deepcopy(unordered_bytes_table), "bytes are in wrong order"),
                                           (deepcopy(healthy_bytes_table), ""),
                                           (deepcopy(half_bytes_table), "")])
def test_check_order(table, result, caplog):
    table.check_order()
    if result == "":
        assert caplog.text == ""
    else:
        assert result in caplog.text


@pytest.mark.parametrize("table, result, type", [(deepcopy(bits_table), "sum of bits is not a power of 2", "bits"),
                                                 (deepcopy(healthy_bits_table), "", "bits"),
                                                 (deepcopy(half_bits_table), "sum of bits is not a power of 2", "bits"),
                                                 (deepcopy(bytes_table), "sum of bytes is not a power of 2", "bytes"),
                                                 (deepcopy(healthy_bytes_table), "", "bytes"),
                                                 (deepcopy(half_bytes_table), "sum of bytes is not a power of 2", "bytes")])
def test_check_sum(table, result, type, caplog):
    table.calculate_bits_and_bytes(type)
    table.check_sum(type)
    if result == "":
        assert caplog.text == ""
    else:
        assert result in caplog.text


@pytest.mark.parametrize("table, result, type", [(deepcopy(bits_table), "overlap of bits", "bits"),
                                                 (deepcopy(healthy_bits_table), "", "bits"),
                                                 (deepcopy(half_bits_table), "", "bits"),
                                                 (deepcopy(bytes_table), "overlap of bytes", "bytes"),
                                                 (deepcopy(half_bytes_table), "", "bytes"),
                                                 (deepcopy(healthy_bytes_table), "", "bytes")])
def test_check_overlap(table, result, type, caplog):
    table.check_overlap(type)
    if result == "":
        assert caplog.text == ""
    else:
        assert result in caplog.text


@pytest.mark.parametrize("table, result, type", [(deepcopy(bits_table), "hole in bits", "bits"),
                                                 (deepcopy(healthy_bits_table), "", "bits"),
                                                 (deepcopy(half_bits_table), "", "bits"),
                                                 (deepcopy(bytes_table), "hole in bytes", "bytes"),
                                                 (deepcopy(half_bytes_table), "", "bytes"),
                                                 (deepcopy(healthy_bytes_table), "", "bytes")])
def test_check_for_holes(table, result, type, caplog):
    table.check_for_holes(type)
    if result == "":
        assert caplog.text == ""
    else:
        assert result in caplog.text


def test_detect_hex_columns():
    undetected_hex_table_1 = transformer.Table("test table", [
        {"value": "20h", "description": "This shouldn't be changed 20h"},
        {"value": "80h", "description": "80h This shouldn't be changed"},
        {"value": "90h", "description": "This shouldn't 90h be changed"},
    ])

    detected_hex_table_1 = transformer.Table("test table", [
        {"hex-value": "20h", "description": "This shouldn't be changed 20h"},
        {"hex-value": "80h", "description": "80h This shouldn't be changed"},
        {"hex-value": "90h", "description": "This shouldn't 90h be changed"},
    ])

    undetected_hex_table_2 = transformer.Table("test table", [
        {"heading with spaces": "30h to F0h", "description": "This shouldn't be changed 30h to F0h"},
        {"heading with spaces": "F1h to FAh", "description": "F1h to FAh This shouldn't be changed"},
        {"heading with spaces": "FBh to 1AAh", "description": "This shouldn't FBh to 1AAh be changed"},
    ])
    detected_hex_table_2 = transformer.Table("test table", [
        {"hex-heading with spaces": "30h to F0h", "description": "This shouldn't be changed 30h to F0h"},
        {"hex-heading with spaces": "F1h to FAh", "description": "F1h to FAh This shouldn't be changed"},
        {"hex-heading with spaces": "FBh to 1AAh", "description": "This shouldn't FBh to 1AAh be changed"},
    ])

    undetected_hex_table_3 = transformer.Table("test table", [
        {"w3i?d he4d1/g": "ABh"},
        {"w3i?d he4d1/g": "80Ah"},
        {"w3i?d he4d1/g": "All Others"},
    ])
    detected_hex_table_3 = transformer.Table("test table", [
        {"hex-w3i?d he4d1/g": "ABh"},
        {"hex-w3i?d he4d1/g": "80Ah"},
        {"hex-w3i?d he4d1/g": "All Others"},
    ])

    undetected_hex_table_1.detect_hex_columns()
    undetected_hex_table_2.detect_hex_columns()
    undetected_hex_table_3.detect_hex_columns()

    assert(undetected_hex_table_1.rows == detected_hex_table_1.rows)
    assert(undetected_hex_table_1.headings == detected_hex_table_1.headings)
    assert(undetected_hex_table_2.rows == detected_hex_table_2.rows)
    assert(undetected_hex_table_2.headings == detected_hex_table_2.headings)
    assert(undetected_hex_table_3.rows == detected_hex_table_3.rows)
    assert(undetected_hex_table_3.headings == detected_hex_table_3.headings)

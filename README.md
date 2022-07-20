# nvme-lint

`nvme-lint` is a tool that uses [Camelot-py](https://github.com/camelot-dev/camelot) and [Poppler](https://github.com/freedesktop/poppler) to validate tables in NVMe specification documents.

## Getting started

### Dependencies
On Debian these packages are required:
```
  python
  pip
  poppler-utils
  libgl1
```

Before you can start using `nvme-lint` you must have `pdftohtml` in your PATH.
Write the command `pdftohtml -v` to verify that it is available.

### Installation

- Install by running:
```
  pip install nvme-lint
```

### Usage

To validate a NVMe specification file run the command:
```
  nvme-lint file_name
``` 

You can also run the tool directly from the source directory with the command:

```
  python -m nvme_lint
```

## How it works
nvme-lint will extract every table from a NVMe specification pdf file, unless a target- or ignore-file is provided.
Afterwards, it will proceed to parse and validate the tables.

The flags for `nvme-lint` are defined below:
```
  usage: nvme-lint [-h] [-l LOG] [-i IGNORE] [-t TARGET] [-y] file

  positional arguments:
    file                  
        The pdf file containing the tables to validate

  options:
    -h, --help            
        show this help message and exit
        
    -l LOG, --log LOG     
        The logging level. Possible values in order of severity: DEBUG, INFO, WARNING, ERROR, CRITICAL

    -i IGNORE, --ignore IGNORE
        A .txt file containing figure numbers to ignore, each number should go on a separate line.
        This file will be ignored if a target is specified

    -t TARGET, --target TARGET
        A .txt file containing figure numbers to validate, each number should go on a separate line. 
        If this file is specified only the figure numbers included will be validated

    -y, --yaml 
        If this flag is set, the content of the tables will be written to 'output.yaml' 
        NOTE: If you have a file called `output.yaml` in the directory you call `nvme-lint` from, it will be overwritten
```

### Validation
During the process `nvme-lint` checks for the following:

| Issue                                                             | Log message                                                      |
|-------------------------------------------------------------------|------------------------------------------------------------------|
| Incorrect format for the table captions                           | Encountered a problem with the caption to Figure (figure number) |
| Incorrect format of footnotes                                     | (value) should be 'NOTES'                                        |
| Columns called 'bit' instead of 'bits'                            | 'bit' instead of 'bits'                                          |
| Columns called 'byte' instead of 'bytes'                          | 'byte' instead of 'bytes'                                        |
| Incorrect format for bit- and byte-ranges (n to m instead of m:n) | (bytes / bits) range is of the wrong format: (value)             |
| Hexadecimal values in bits- and bytes-columns                     | (bytes / bits) value is of the wrong type: (value)               |
| Incorrect ordering for bits- and bytes-columns                    | (bytes / bits) are in wrong order                                |
| Incorrect ordering for bits- and bytes-ranges                     | (bytes / bits) range is in wrong order: (value)                  |
| Overlapping bits or bytes                                         | overlap of (bytes / bits)                                        |
| Holes in the bits or bytes                                        | hole in (bytes / bits)                                           |
| Incorrect sum of bits or bytes (not a power of 2)                 | sum of (bytes / bits) is not a power of 2                        |
| Incorrect sum of bits for commands                                | bits doesn't sum up to (32 / 64)                                 |


### Logging
The messages from `nvme-lint` will be outputted to the terminal and the file `nvme-lint.log`.
This file is placed in `$XDG_DATA_HOME/nvme-lint/`, if `$XDG_DATA_HOME` is in the environment. Otherwise, it will be placed in `~/.local/share/nvme-lint/`.

## License
All software contained within this repository is dual licensed under the GNU General Public License version 2 or later or the Apache-2.0 license. See COPYING and LICENSE for more information.

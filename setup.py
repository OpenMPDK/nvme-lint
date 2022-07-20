import os

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nvme-lint",
    version="0.1.2",
    author="Karl Bonde Torp",
    author_email="k.torp@samsung.com",
    description="Validate content of NVMe specification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenMPDK/nvme-lint",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "camelot-py[cv]",
        "pyyaml"
    ],
    package_dir={"": "./"},
    packages=find_packages(),
    entry_points={
         "console_scripts": ["nvme-lint = nvme_lint.__main__:main", ],
    },
)

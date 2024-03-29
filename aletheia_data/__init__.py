#!/usr/bin/env python
"""Top-level module for aletheia-data ."""
from pkg_resources import DistributionNotFound, get_distribution

from . import config
from .core import AletheiaPooch, create
from .downloaders import Downloader

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

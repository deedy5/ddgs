"""
DDGS (Dux Distributed Global Search) metasearch engine.
"""

import logging

from .ddgs import DDGS
from .version import __version__

__all__ = ["DDGS", "__version__", "cli"]


# A do-nothing logging handler
# https://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("ddgs").addHandler(logging.NullHandler())

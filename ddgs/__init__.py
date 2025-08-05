import logging

from .ddgs import DDGS

__version__ = "9.5.2"
__all__ = ("DDGS",)


# A do-nothing logging handler
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("ddgs").addHandler(logging.NullHandler())

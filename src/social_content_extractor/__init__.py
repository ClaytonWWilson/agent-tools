"""
Social Content Extractor

A CLI tool for extracting content information from Instagram and YouTube posts.
"""

from .extractor import ContentExtractor
from .cli import main

__version__ = "0.3.0"
__all__ = ["ContentExtractor", "main"]

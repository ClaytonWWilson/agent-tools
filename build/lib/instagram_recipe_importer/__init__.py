"""
Instagram Recipe Importer

A CLI tool for extracting recipe information from Instagram and YouTube posts.
"""

from .extractor import RecipeExtractor
from .cli import main

__version__ = "0.2.0"
__all__ = ["RecipeExtractor", "main"]

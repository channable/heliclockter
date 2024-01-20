"""
Configuration of test directory

This is picked up and handled by pytest, which ensures this is imported first,
therefore we can adjust the import paths here.

We ensure that heliclockter is picked up from the src directory of the project
in development rather than a potentially already installed package.
Inserting the path to the `src` directory (resolved to an absolute path) at the
beginning of `sys.path` is sufficient.
"""

from __future__ import annotations as __annotations

import importlib as __importlib
import sys as __sys
from pathlib import Path as __Path

__sys.path.insert(0, str((__Path(__file__).parent / '..' / 'src').resolve()))
__importlib.import_module('heliclockter')

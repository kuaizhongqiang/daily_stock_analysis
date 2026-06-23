# -*- coding: utf-8 -*-
"""Pytest configuration — minimal setup for dsa-server offline tests."""
from __future__ import annotations

import os
import sys

# Ensure the project root is on sys.path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

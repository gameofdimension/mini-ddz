"""Pytest configuration file."""

import os
import sys

# Add pve_server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pve_server"))

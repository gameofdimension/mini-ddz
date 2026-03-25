"""Pytest configuration file."""
import sys
import os

# Add pve_server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pve_server'))

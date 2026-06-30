"""Pytest configuration for opc_simulator tests.

Adds the opc_simulator directory to ``sys.path`` so test modules can import
``common``, ``simulator``, ``web_server`` etc. without package install.
"""
import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

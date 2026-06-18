"""
f1_analysis
===========

A toolkit for analyzing Formula 1 telemetry and timing data using the
FastF1 API. Provides utilities for single-session deep dives, season-level
comparisons, and driver head-to-head telemetry analysis.

Quick start:

    from f1_analysis.core.session_loader import load_session

    session = load_session(2024, "Monza", "R")
    laps = session.laps

See the README and `scripts/` directory for runnable examples.
"""

__version__ = "0.1.0"

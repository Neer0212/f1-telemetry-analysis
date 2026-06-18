"""
Markdown report generation.

Turns a loaded session into a self-contained Markdown summary: session
metadata, fastest laps, race pace summary, and tire strategy overview.
Intended as a quick, shareable text artifact alongside the charts
produced by ``f1_analysis.visualization``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd
from fastf1.core import Session

from f1_analysis.core.lap_analysis import (
    clean_lap_times,
    fastest_laps_by_driver,
    race_pace_summary,
    stint_summary,
)


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a Markdown table without extra dependencies."""
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        values = [f"{v:.3f}" if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def generate_session_report(
    session: Session,
    *,
    output_path: Optional[Union[str, Path]] = None,
) -> str:
    """
    Generate a Markdown summary report for a session.

    Parameters
    ----------
    session:
        A loaded FastF1 session.
    output_path:
        If provided, the report is also written to this file path.

    Returns
    -------
    str
        The generated Markdown report as a string.
    """
    event = session.event
    clean_laps = clean_lap_times(session.laps)

    fastest = fastest_laps_by_driver(clean_laps)[["Driver", "Team", "LapTimeSeconds", "Compound"]].copy()
    fastest["LapTimeSeconds"] = fastest["LapTimeSeconds"].round(3)

    pace = race_pace_summary(clean_laps).round(3)
    strategy = stint_summary(session.laps)
    strategy["AvgLapTime"] = strategy["AvgLapTime"].round(3)

    weather_summary = ""
    if session.weather_data is not None and not session.weather_data.empty:
        w = session.weather_data
        weather_summary = (
            f"- Air temperature: {w['AirTemp'].mean():.1f} °C (avg)\n"
            f"- Track temperature: {w['TrackTemp'].mean():.1f} °C (avg)\n"
            f"- Humidity: {w['Humidity'].mean():.1f}% (avg)\n"
            f"- Rainfall observed: {'Yes' if w['Rainfall'].any() else 'No'}\n"
        )

    report = f"""# Session Report — {event['EventName']} {event.year}

**Session:** {session.name}
**Location:** {event['Location']}, {event['Country']}
**Date:** {session.date}

## Weather

{weather_summary or "_Weather data not available for this session._"}

## Fastest Laps

{_df_to_markdown_table(fastest)}

## Race Pace Summary (mean / median / std of clean laps, seconds)

{_df_to_markdown_table(pace)}

## Tire Strategy

{_df_to_markdown_table(strategy)}

---
*Generated with f1-telemetry-analysis using the FastF1 API.*
"""

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")

    return report

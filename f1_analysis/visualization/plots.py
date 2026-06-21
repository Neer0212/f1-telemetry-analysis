"""
Chart-generating functions.

Each function here takes already-loaded FastF1 data (sessions, laps,
telemetry DataFrames) and produces a single Matplotlib figure. Functions
return the ``Figure`` object rather than saving directly, so callers
(scripts, notebooks) decide whether to display, save, or further modify
the chart. See ``scripts/`` for examples that save these to disk.
"""

from __future__ import annotations

from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fastf1.core import Session
from matplotlib.figure import Figure

from f1_analysis.core.lap_analysis import clean_lap_times, laps_to_seconds, stint_summary
from f1_analysis.core.telemetry import TelemetryComparison
from f1_analysis.visualization.style import (
    get_compound_color,
    get_driver_style,
    get_driver_color,
    get_team_color,
)


def plot_lap_time_distribution(
    session: Session,
    drivers: Sequence[str],
    *,
    title: Optional[str] = None,
) -> Figure:
    """
    Box/violin-style comparison of lap time distribution for several drivers.

    Useful for comparing race pace consistency: a tight, low distribution
    indicates strong consistent pace, while a wide spread suggests
    inconsistency (traffic, tire issues, mistakes).

    Parameters
    ----------
    session:
        A loaded FastF1 session (typically a race for pace analysis).
    drivers:
        Driver abbreviations to include, e.g. ``["VER", "HAM", "LEC"]``.
    title:
        Optional custom title. Defaults to a description based on the
        session.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    data = []
    labels = []
    colors = []
    for driver in drivers:
        driver_laps = clean_lap_times(session.laps.pick_drivers(driver))
        if driver_laps.empty:
            continue
        data.append(laps_to_seconds(driver_laps).dropna().values)
        labels.append(driver)
        colors.append(get_driver_color(driver, session))

    parts = ax.violinplot(data, showmedians=True)
    for body, color in zip(parts["bodies"], colors):
        body.set_facecolor(color)
        body.set_alpha(0.7)

    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Lap Time (s)")
    ax.set_title(
        title
        or f"Lap Time Distribution — {session.event['EventName']} {session.event.year} {session.name}"
    )
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_race_pace(
    session: Session,
    drivers: Sequence[str],
    *,
    rolling_window: int = 3,
    title: Optional[str] = None,
) -> Figure:
    """
    Lap-by-lap race pace line chart for several drivers, with a rolling average.

    The raw per-lap line is noisy (traffic, fuel load, tire phase), so a
    rolling mean is overlaid to show the underlying pace trend -- this is
    the standard way to visually compare race pace/degradation between
    drivers across a race distance.

    Parameters
    ----------
    session:
        A loaded FastF1 race session.
    drivers:
        Driver abbreviations to include.
    rolling_window:
        Window size (in laps) for the rolling average overlay.
    title:
        Optional custom title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    for driver in drivers:
        driver_laps = clean_lap_times(session.laps.pick_drivers(driver))
        if driver_laps.empty:
            continue
        lap_seconds = laps_to_seconds(driver_laps)
        style = get_driver_style(driver, session)

        ax.plot(
            driver_laps["LapNumber"],
            lap_seconds.rolling(rolling_window, min_periods=1).mean(),
            label=driver,
            linewidth=2,
            **style,
        )
        ax.scatter(driver_laps["LapNumber"], lap_seconds, alpha=0.15, s=15, color=style.get("color"))

    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time (s)")
    ax.set_title(
        title
        or f"Race Pace — {session.event['EventName']} {session.event.year} ({rolling_window}-lap rolling avg)"
    )
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_tire_strategy(session: Session, drivers: Optional[Sequence[str]] = None) -> Figure:
    """
    Horizontal bar chart of each driver's tire strategy (stint compounds and lengths).

    Reconstructs the classic "strategy chart" seen in race broadcasts:
    one horizontal bar per driver, segmented by stint, colored by
    compound, sized by stint length.

    Parameters
    ----------
    session:
        A loaded FastF1 race session.
    drivers:
        Optional subset of driver abbreviations. Defaults to all drivers
        in finishing order.

    Returns
    -------
    matplotlib.figure.Figure
    """
    stints = stint_summary(session.laps)

    if drivers is not None:
        stints = stints[stints["Driver"].isin(drivers)]
        driver_order = list(drivers)
    else:
        # Order by finishing position if available, else by driver code.
        try:
            results = session.results.sort_values("Position")
            driver_order = [d for d in results["Abbreviation"] if d in stints["Driver"].unique()]
        except Exception:  # noqa: BLE001
            driver_order = sorted(stints["Driver"].unique())

    fig, ax = plt.subplots(figsize=(12, max(4, len(driver_order) * 0.4)))

    for y_pos, driver in enumerate(driver_order):
        driver_stints = stints[stints["Driver"] == driver]
        left = 0
        for _, stint in driver_stints.iterrows():
            color = get_compound_color(stint["Compound"], session)
            ax.barh(
                y_pos,
                stint["LapCount"],
                left=left,
                color=color,
                edgecolor="black",
                linewidth=0.5,
            )
            left += stint["LapCount"]

    ax.set_yticks(range(len(driver_order)))
    ax.set_yticklabels(driver_order)
    ax.invert_yaxis()
    ax.set_xlabel("Lap Number")
    ax.set_title(f"Tire Strategy — {session.event['EventName']} {session.event.year}")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    return fig


def plot_speed_trace_comparison(comparison, session):
    fig, ax = plt.subplots(figsize=(12, 5))
    
    color_a = get_driver_color(comparison.driver_a, session)
    color_b = get_driver_color(comparison.driver_b, session)
    
    # Default line styles
    style_a = "-"
    style_b = "-"
    
    # If they are teammates, make driver_b stand out with a dashed line
    if color_a == color_b:
        style_b = "--" 
        # Optional: you can also make it slightly lighter if preferred:
        # import matplotlib.colors as mcolors
        # color_b = mcolors.to_rgba(color_b, alpha=0.7)

    # Plot Driver A
    ax.plot(
        comparison.telemetry_a["Distance"], 
        comparison.telemetry_a["Speed"], 
        color=color_a, 
        linestyle=style_a,
        label=comparison.driver_a, 
        linewidth=2
    )
    
    # Plot Driver B
    ax.plot(
        comparison.telemetry_b["Distance"], # FIX: Changed from telemetry_a to telemetry_b
        comparison.telemetry_b["Speed"], 
        color=color_b, 
        linestyle=style_b,
        label=comparison.driver_b, 
        linewidth=2
    )
    
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Speed (km/h)")
    ax.set_title(f"Speed Trace: {comparison.driver_a} vs {comparison.driver_b}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_telemetry_delta(comparison: TelemetryComparison, session: Session) -> Figure:
    """
    Plot cumulative time delta between two drivers across a lap.

    Shows exactly where on track one driver gains or loses time relative
    to the other. The line crossing zero indicates the overtake/swap
    point in cumulative pace; a generally upward-or-downward slope shows
    sustained advantage in that section.

    Parameters
    ----------
    comparison:
        Output of :func:`f1_analysis.core.telemetry.compare_driver_telemetry`.
    session:
        The session the comparison was generated from (for team colors).

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(12, 4))

    color_b = get_driver_color(comparison.driver_b, session)
    
    ax.plot(comparison.delta_time["Distance"], comparison.delta_time["Delta"], color=color_b, linewidth=2)
    ax.axhline(0, color="white", linewidth=0.8, alpha=0.5, linestyle="--")
    ax.fill_between(
        comparison.delta_time["Distance"],
        comparison.delta_time["Delta"],
        0,
        alpha=0.2,
        color=color_b,
    )

    ax.set_xlabel("Distance (m)")
    ax.set_ylabel(f"<- {comparison.driver_a} ahead | {comparison.driver_b} ahead ->")
    ax.set_title(f"Time Delta — {comparison.driver_a} vs {comparison.driver_b}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_throttle_brake_comparison(comparison: TelemetryComparison, session: Session) -> Figure:
    """
    Stacked throttle % and brake traces for two drivers across a lap.

    Reveals driving-style differences underlying a speed-trace gap, e.g.
    later/harder braking, earlier throttle application out of a corner.

    Parameters
    ----------
    comparison:
        Output of :func:`f1_analysis.core.telemetry.compare_driver_telemetry`.
    session:
        The session the comparison was generated from (for team colors).

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    style_a = get_driver_style(comparison.driver_a, session)
    style_b = get_driver_style(comparison.driver_b, session)

    axes[0].plot(comparison.telemetry_a["Distance"], comparison.telemetry_a["Throttle"], label=comparison.driver_a, **style_a)
    axes[0].plot(comparison.telemetry_b["Distance"], comparison.telemetry_b["Throttle"], label=comparison.driver_b, **style_b)
    axes[0].set_ylabel("Throttle (%)")
    axes[0].legend(loc="lower right")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(comparison.telemetry_a["Distance"], comparison.telemetry_a["Brake"].astype(int) * 100, **style_a)
    axes[1].plot(comparison.telemetry_b["Distance"], comparison.telemetry_b["Brake"].astype(int) * 100, **style_b)
    axes[1].set_ylabel("Brake")
    axes[1].set_xlabel("Distance (m)")
    axes[1].grid(True, alpha=0.3)

    fig.suptitle(f"Throttle & Brake — {comparison.driver_a} vs {comparison.driver_b}")
    fig.tight_layout()
    return fig


def plot_championship_progression(
    standings: pd.DataFrame,
    *,
    entity_column: str = "DriverCode",
    top_n: Optional[int] = None,
    title: str = "Championship Progression",
) -> Figure:
    """
    Line chart of championship points accumulated round-by-round.

    Works for either driver or constructor standings -- pass the
    DataFrame produced by
    :func:`f1_analysis.core.season.build_driver_standings_progression` or
    :func:`f1_analysis.core.season.build_team_standings_progression`.

    Parameters
    ----------
    standings:
        Long-format standings DataFrame with ``Round``, ``Points``, and
        an entity column (driver or constructor).
    entity_column:
        Which column identifies each line, e.g. ``"DriverCode"`` or
        ``"Constructor"``.
    top_n:
        If set, only plot the top N entities by final points total
        (keeps the chart readable for a full driver grid).
    title:
        Chart title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    if top_n is not None:
        final_round = standings["Round"].max()
        top_entities = (
            standings[standings["Round"] == final_round]
            .sort_values("Points", ascending=False)[entity_column]
            .head(top_n)
        )
        standings = standings[standings[entity_column].isin(top_entities)]

    entities = sorted(standings[entity_column].unique())

    # Guaranteed distinct colors for up to 40 entities using two colormaps
    import matplotlib.cm as _cm
    _pool = [_cm.tab20(i) for i in range(20)] + [_cm.tab20b(i) for i in range(20)]
    color_map = {e: _pool[i % len(_pool)] for i, e in enumerate(entities)}
    linestyles = ["-", "--", "-.", ":"]

    for i, (entity, group) in enumerate(standings.groupby(entity_column)):
        group = group.sort_values("Round")
        ax.plot(
            group["Round"], group["Points"],
            marker="o", markersize=3, label=entity, linewidth=2,
            color=color_map[entity],
            linestyle=linestyles[i % len(linestyles)],
        )

    ax.set_xlabel("Round")
    ax.set_ylabel("Points")
    ax.set_title(title)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_track_speed_map(telemetry: pd.DataFrame, session: Session, driver: str) -> Figure:
    """
    Plot the track outline colored by speed at each point (a "speed map").

    Uses the lap's X/Y position channels to draw the actual circuit
    shape, colored by speed -- a visually intuitive way to see where on
    track a driver is fastest/slowest.

    Parameters
    ----------
    telemetry:
        Telemetry DataFrame with ``X``, ``Y``, and ``Speed`` columns
        (as returned by ``get_driver_telemetry``).
    session:
        The session (used for the title only).
    driver:
        Driver abbreviation (used for the title only).

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(9, 9))

    points = np.array([telemetry["X"], telemetry["Y"]]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    from matplotlib.collections import LineCollection

    norm = plt.Normalize(telemetry["Speed"].min(), telemetry["Speed"].max())
    lc = LineCollection(segments, cmap="plasma", norm=norm, linewidth=4)
    lc.set_array(telemetry["Speed"])
    line = ax.add_collection(lc)

    ax.set_xlim(telemetry["X"].min() - 200, telemetry["X"].max() + 200)
    ax.set_ylim(telemetry["Y"].min() - 200, telemetry["Y"].max() + 200)
    ax.set_aspect("equal")
    ax.axis("off")

    cbar = fig.colorbar(line, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("Speed (km/h)")

    ax.set_title(f"Speed Map — {driver} — {session.event['EventName']} {session.event.year}")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# ML visualization functions
# ---------------------------------------------------------------------------

def plot_feature_importances(importances: pd.DataFrame, title: str = "Feature Importances") -> Figure:
    """
    Horizontal bar chart of model feature importances.

    Parameters
    ----------
    importances:
        DataFrame with ``Feature`` and ``Importance`` columns, as returned
        by ``model.feature_importances()``.
    title:
        Chart title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(9, max(4, len(importances) * 0.35)))
    importances = importances.sort_values("Importance", ascending=True)
    ax.barh(importances["Feature"], importances["Importance"], color="#3671C6", alpha=0.85)
    ax.set_xlabel("Importance")
    ax.set_title(title)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    return fig


def plot_degradation_curve(
    degradation_df: pd.DataFrame,
    compound: str,
    title: Optional[str] = None,
) -> Figure:
    """
    Plot the predicted lap time degradation curve for a tire compound.

    Parameters
    ----------
    degradation_df:
        DataFrame with ``TyreLife`` and ``PredictedLapTime`` columns,
        as returned by ``LapTimePredictor.degradation_curve()``.
    compound:
        Compound name (for label and color).
    title:
        Optional custom title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    COMPOUND_COLORS = {
        "SOFT": "#DA291C",
        "MEDIUM": "#FFD700",
        "HARD": "#FFFFFF",
        "INTERMEDIATE": "#43B02A",
        "WET": "#0067AD",
    }
    color = COMPOUND_COLORS.get(compound.upper(), "#888888")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(
        degradation_df["TyreLife"],
        degradation_df["PredictedLapTime"],
        color=color,
        linewidth=2.5,
        marker="o",
        markersize=4,
        label=f"{compound.capitalize()} compound",
    )
    ax.set_xlabel("Tyre Life (laps)")
    ax.set_ylabel("Predicted Lap Time (s)")
    ax.set_title(title or f"Predicted Tyre Degradation — {compound.capitalize()}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_undercut_windows(scored_laps: pd.DataFrame, event_name: str = "") -> Figure:
    """
    Scatter plot of undercut score over lap number, with flagged windows highlighted.

    Parameters
    ----------
    scored_laps:
        Output of ``UndercutDetector.score_laps()`` for a single race.
    event_name:
        Used in the chart title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    if "Driver" in scored_laps.columns:
        for driver, grp in scored_laps.groupby("Driver"):
            mask = grp["WindowOpen"]
            ax.scatter(
                grp["LapNumber"], grp["UndercutScore"],
                s=18, alpha=0.35, color="grey",
            )
            ax.scatter(
                grp.loc[mask, "LapNumber"], grp.loc[mask, "UndercutScore"],
                s=55, alpha=0.9, label=driver, zorder=5,
            )
    else:
        ax.scatter(scored_laps["LapNumber"], scored_laps["UndercutScore"], s=18, alpha=0.5)
        mask = scored_laps["WindowOpen"]
        ax.scatter(scored_laps.loc[mask, "LapNumber"], scored_laps.loc[mask, "UndercutScore"],
                   s=60, color="red", label="Window Open", zorder=5)

    ax.axhline(0.6, color="red", linewidth=1, linestyle="--", alpha=0.7, label="Threshold (0.6)")
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Undercut Score")
    ax.set_ylim(0, 1.05)
    ax.set_title(f"Undercut Windows — {event_name}")
    ax.legend(loc="upper right", fontsize=8, ncol=3)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_compound_confusion(
    y_true: "Sequence[str]",
    y_pred: "Sequence[str]",
) -> Figure:
    """
    Confusion matrix heatmap for the tire compound classifier.

    Parameters
    ----------
    y_true:
        True compound labels.
    y_pred:
        Predicted compound labels from ``TireCompoundClassifier.predict()``.

    Returns
    -------
    matplotlib.figure.Figure
    """
    from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

    classes = sorted(set(list(y_true) + list(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=classes)

    fig, ax = plt.subplots(figsize=(7, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes)
    disp.plot(ax=ax, colorbar=True, cmap="Blues")
    ax.set_title("Tire Compound Classifier — Confusion Matrix")
    fig.tight_layout()
    return fig
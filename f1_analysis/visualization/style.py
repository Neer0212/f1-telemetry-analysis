"""
Plot styling utilities.

FastF1 ships official team, driver, and tire compound colors plus a
Matplotlib theme via ``fastf1.plotting``. This module is a thin wrapper
around it so the rest of the codebase has one place to get consistent
F1-branded styling, and so the dependency on FastF1's plotting internals
is isolated to a single file.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import fastf1.plotting as f1_plotting
from fastf1.core import Session

_STYLE_APPLIED = False


def apply_f1_style() -> None:
    """
    Apply FastF1's matplotlib color scheme and timedelta tick support.

    Idempotent -- safe to call multiple times (e.g. once per script).
    Sets a dark, F1-broadcast-inspired theme and enables FastF1's
    Timple-based formatting so Timedelta lap times plot correctly on
    an axis without manual conversion.
    """
    global _STYLE_APPLIED
    f1_plotting.setup_mpl(mpl_timedelta_support=True, color_scheme="fastf1")
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.dpi"] = 200
    plt.rcParams["savefig.bbox"] = "tight"
    _STYLE_APPLIED = True


def get_team_color(team: str, session: Session) -> str:
    """
    Get a team's official color (hex) for the given session's season.

    Team colors can change between seasons (liveries, rebrands), which
    is why FastF1 requires a session for context rather than a static
    lookup table.

    Parameters
    ----------
    team:
        A recognizable part of the team name, e.g. ``"Red Bull"``,
        ``"Ferrari"``, ``"Mercedes"``.
    session:
        The session providing season context.

    Returns
    -------
    str
        Hex color code, e.g. ``"#3671C6"``.
    """
    return f1_plotting.get_team_color(team, session)


def get_driver_color(driver: str, session: Session) -> str:
    """
    Get the color associated with a driver (i.e. their team's color).

    Note that teammates share a color -- use :func:`get_driver_style`
    or ``fastf1.plotting.get_driver_style`` when comparing two drivers
    from the same team, so line style/markers differentiate them.

    Parameters
    ----------
    driver:
        Driver abbreviation (e.g. ``"VER"``) or recognizable name part.
    session:
        The session providing season/team context.

    Returns
    -------
    str
        Hex color code.
    """
    return f1_plotting.get_driver_color(driver, session)


def get_driver_style(driver: str, session: Session, style: list | None = None) -> dict:
    """
    Get a unique Matplotlib style dict for a driver (color + line style).

    Use this instead of :func:`get_driver_color` when plotting multiple
    drivers, especially teammates, so each line is visually distinct
    even when the underlying team color is identical.

    Parameters
    ----------
    driver:
        Driver abbreviation (e.g. ``"VER"``).
    session:
        The session providing season/team context.
    style:
        Optional list of style keys to vary, e.g. ``["color", "linestyle"]``.
        Defaults to FastF1's built-in default styling options.

    Returns
    -------
    dict
        Keyword arguments ready to unpack into a Matplotlib plot call,
        e.g. ``ax.plot(x, y, **get_driver_style("VER", session))``.
    """
    style = style or ["color", "linestyle"]
    return f1_plotting.get_driver_style(driver, style, session)


def get_compound_color(compound: str, session: Session) -> str:
    """
    Get the official tire compound color (e.g. red for Soft, yellow for Medium).

    Parameters
    ----------
    compound:
        Compound name as used by FastF1: ``"SOFT"``, ``"MEDIUM"``,
        ``"HARD"``, ``"INTERMEDIATE"``, ``"WET"``.
    session:
        The session providing season context (compound colors are
        stable, but the API requires a session for consistency).

    Returns
    -------
    str
        Hex color code.
    """
    return f1_plotting.get_compound_color(compound, session)

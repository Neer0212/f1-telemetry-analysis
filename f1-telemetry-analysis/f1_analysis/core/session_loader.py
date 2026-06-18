"""
Session loading utilities.

Wraps ``fastf1.get_session`` with sensible defaults: automatic cache
configuration, clear error messages, and a single entry point so the
rest of the codebase never talks to the raw FastF1 API directly.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional, Union

import fastf1

logger = logging.getLogger(__name__)

# Identifiers FastF1 understands for the `identifier` argument of get_session.
SessionIdentifier = Literal[
    "FP1", "FP2", "FP3", "Q", "S", "SS", "SQ", "R",
    "Practice 1", "Practice 2", "Practice 3",
    "Qualifying", "Sprint", "Sprint Shootout", "Sprint Qualifying", "Race",
]

_CACHE_ENABLED = False


def enable_cache(cache_dir: Union[str, Path] = "cache") -> Path:
    """
    Turn on FastF1's local disk cache.

    FastF1 re-downloads session data every time it isn't cached, and a
    single race weekend (laps + car + position data) can be tens of
    megabytes. Caching makes repeated analysis and notebook re-runs fast
    and avoids hammering the upstream data source.

    Parameters
    ----------
    cache_dir:
        Directory used to store cached session data. Created if it does
        not already exist.

    Returns
    -------
    Path
        The resolved cache directory.
    """
    global _CACHE_ENABLED
    cache_path = Path(cache_dir).resolve()
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))
    _CACHE_ENABLED = True
    logger.info("FastF1 cache enabled at %s", cache_path)
    return cache_path


def load_session(
    year: int,
    grand_prix: Union[str, int],
    session_identifier: SessionIdentifier = "R",
    *,
    laps: bool = True,
    telemetry: bool = True,
    weather: bool = True,
    messages: bool = False,
    cache_dir: Union[str, Path] = "cache",
) -> fastf1.core.Session:
    """
    Load a single F1 session with its data populated.

    This is the single entry point the rest of the package uses to reach
    FastF1, so caching and error handling are applied consistently.

    Parameters
    ----------
    year:
        Championship season, e.g. ``2024``.
    grand_prix:
        Event name (fuzzy-matched, e.g. ``"Monza"``, ``"Silverstone"``,
        ``"Abu Dhabi"``) or round number (e.g. ``5``).
    session_identifier:
        Which session to load. Common values: ``"FP1"``, ``"FP2"``,
        ``"FP3"``, ``"Q"`` (qualifying), ``"S"`` (sprint), ``"R"`` (race).
    laps, telemetry, weather, messages:
        Forwarded to ``Session.load`` to control which data streams are
        fetched. Disabling unused streams speeds up loading noticeably.
    cache_dir:
        Where to store/read cached data. Cache is enabled automatically
        on first call.

    Returns
    -------
    fastf1.core.Session
        A loaded FastF1 session, ready for lap/telemetry analysis.

    Raises
    ------
    RuntimeError
        If the session cannot be found or data fails to load (wraps the
        underlying FastF1 exception with a clearer message).
    """
    if not _CACHE_ENABLED:
        enable_cache(cache_dir)

    try:
        session = fastf1.get_session(year, grand_prix, session_identifier)
    except Exception as exc:  # noqa: BLE001 - re-raised with context below
        raise RuntimeError(
            f"Could not resolve session: year={year}, gp={grand_prix!r}, "
            f"session={session_identifier!r}. Check the event name/round "
            f"and that the season/session has taken place. "
            f"Original error: {exc}"
        ) from exc

    try:
        session.load(laps=laps, telemetry=telemetry, weather=weather, messages=messages)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Found the session ({session.event['EventName']} {year} "
            f"{session_identifier}) but failed to load its data. This "
            f"usually means the session hasn't happened yet, or there is "
            f"no network access. Original error: {exc}"
        ) from exc

    logger.info(
        "Loaded %s %s %s (%d laps)",
        year, session.event.get("EventName", grand_prix), session_identifier,
        len(session.laps) if session.laps is not None else 0,
    )
    return session

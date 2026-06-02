"""Fetcher registry — the extension point for new data sources.

New source = new BaseFetcher subclass + one register_fetcher() call.
"""

import logging

logger = logging.getLogger(__name__)

# source_type string -> fetcher class
_REGISTRY: dict = {}


def register_fetcher(source_type: str, fetcher_cls) -> None:
    """Register a fetcher class for a source_type."""
    _REGISTRY[source_type] = fetcher_cls
    logger.debug("Registered fetcher %s for source_type=%s", fetcher_cls.__name__, source_type)


def get_fetcher(source_type: str):
    """Return the fetcher class for a source_type, or None if unregistered."""
    return _REGISTRY.get(source_type)


def registered_source_types() -> list[str]:
    """List all registered source_type strings."""
    return sorted(_REGISTRY.keys())

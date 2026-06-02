"""Source-agnostic data ingestion framework.

Adding a new data source is a configuration exercise, not a plumbing exercise:
write a BaseFetcher subclass, register it in the registry, and create a
DataSource row. The scheduler and status tracking are handled for you.
"""

from citylab.services.ingestion.base import BaseFetcher  # noqa: F401
from citylab.services.ingestion.registry import (  # noqa: F401
    get_fetcher,
    register_fetcher,
)

# Import concrete fetchers so they self-register on package import.
from citylab.services.ingestion import opennem  # noqa: F401,E402
from citylab.services.ingestion import bom  # noqa: F401,E402

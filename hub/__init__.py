"""Vasuki Hub - the unified powerhouse database.

One database, immutable event timeline at the core, knowledge graph,
documents + semantic search, telemetry, projects and projections.
"""

__version__ = "0.1.0"

from hub.vas import Vas

__all__ = ["Vas", "__version__"]
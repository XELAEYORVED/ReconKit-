"""ReconKit recon modules.

Importing this package registers every module in the global ``REGISTRY`` via
``BaseModule.__init_subclass__``. Use :func:`get_registry` to access them.
"""

from __future__ import annotations

from .base import REGISTRY, BaseModule, ModuleResult, get_module, get_registry

# Import each module so its subclass registers itself.
from . import (  # noqa: E402,F401
    whois_lookup,
    dns_enum,
    subdomain_enum,
    cert_transparency,
    tech_detect,
    headers_audit,
    wayback_machine,
    email_harvest,
    social_media,
    metadata_extract,
    google_dorking,
    ip_geolocation,
    reputation,
    leak_check,
    shodan_recon,
    github_recon,
    pastebin_monitor,
    network_map,
)

__all__ = [
    "BaseModule",
    "ModuleResult",
    "REGISTRY",
    "get_module",
    "get_registry",
]

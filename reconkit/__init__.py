"""ReconKit — Passive OSINT reconnaissance toolkit.

ReconKit performs *passive* reconnaissance only: it queries public DNS,
public HTTP endpoints, and public OSINT APIs. It never performs active
scanning, intrusion, fuzzing, or any direct interaction with target
systems beyond publicly available information.
"""

__version__ = "0.1.0"

ETHICAL_BANNER = (
    "ReconKit — Passive OSINT Only. Usage responsable et legal uniquement. / "
    "Responsible and lawful use only."
)

__all__ = ["__version__", "ETHICAL_BANNER"]

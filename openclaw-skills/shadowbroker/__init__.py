"""SistemaHidrico OpenClaw skill package."""
from .sb_signatures import sig
from .sb_query import SistemaHidricoClient

__all__ = ["sig", "SistemaHidricoClient"]

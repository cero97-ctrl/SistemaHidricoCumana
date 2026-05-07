"""SistemaHidrico message signature system.

Every outbound message from the SistemaHidrico AI co-pilot starts with a
branded emoji + text prefix so the user always knows:
  1. It's from the SistemaHidrico app
  2. What TYPE of action is being performed

Usage:
    from sb_signatures import sig
    message = f"{sig('brief')}\\nYour morning intelligence digest..."
"""

# Signature registry — emoji prefix + action label
_SIGNATURES: dict[str, str] = {
    # ── Core Intelligence ──────────────────────────────────────────────
    "brief":       "🌍📡 SISTEMAHIDRICO BRIEF:",
    "warning":     "🌍⚠️ SISTEMAHIDRICO WARNING:",
    "news":        "🌍📰 SISTEMAHIDRICO NEWS:",
    "intel":       "🌍🛰️ SISTEMAHIDRICO INTEL:",
    "update":      "🌍🌐 SISTEMAHIDRICO UPDATE:",

    # ── Search & Discovery ─────────────────────────────────────────────
    "searching":   "🌍🔍 SISTEMAHIDRICO SEARCHING:",
    "pinning":     "🌍📌 SISTEMAHIDRICO PINNING:",
    "geolocate":   "🌍📸 SISTEMAHIDRICO GEOLOCATE:",

    # ── Proximity & Location ───────────────────────────────────────────
    "near_you":    "🌍📍 SISTEMAHIDRICO NEAR YOU:",
    "watching":    "🌍👁️ SISTEMAHIDRICO WATCHING:",

    # ── Threat & Security ──────────────────────────────────────────────
    "threat":      "🌍🔴 SISTEMAHIDRICO THREAT:",
    "sigint":      "🌍📻 SISTEMAHIDRICO SIGINT:",
    "anomaly":     "🌍🔶 SISTEMAHIDRICO ANOMALY:",

    # ── Transport & Movement ───────────────────────────────────────────
    "flight":      "🌍🛫 SISTEMAHIDRICO FLIGHT:",
    "maritime":    "🌍🚢 SISTEMAHIDRICO MARITIME:",
    "satellite":   "🌍🛰️ SISTEMAHIDRICO SATELLITE:",

    # ── Infrastructure ─────────────────────────────────────────────────
    "cyber":       "🌍💻 SISTEMAHIDRICO CYBER:",
    "network":     "🌍🔗 SISTEMAHIDRICO NETWORK:",

    # ── System ─────────────────────────────────────────────────────────
    "online":      "🌍✅ SISTEMAHIDRICO ONLINE:",
    "offline":     "🌍🔴 SISTEMAHIDRICO OFFLINE:",
    "error":       "🌍❌ SISTEMAHIDRICO ERROR:",

    # ── Mesh & Wormhole ────────────────────────────────────────────────
    "mesh":        "🌍📶 SISTEMAHIDRICO MESH:",
    "wormhole":    "🌍🌀 SISTEMAHIDRICO WORMHOLE:",
    "dead_drop":   "🌍💀 SISTEMAHIDRICO DEAD DROP:",

    # ── Time Machine ───────────────────────────────────────────────────
    "timemachine": "🌍🕰️ SISTEMAHIDRICO TIMEMACHINE:",

    # ── Reports ────────────────────────────────────────────────────────
    "report":      "🌍📋 SISTEMAHIDRICO REPORT:",

    # ── SAR (Synthetic Aperture Radar) ─────────────────────────────────
    "sar":         "🌍📡 SISTEMAHIDRICO SAR:",
}


def sig(action: str) -> str:
    """Get the branded signature prefix for an action type.

    Args:
        action: One of the registered action types (brief, warning, news, etc.)

    Returns:
        The full branded signature string, e.g. "🌍📡 SISTEMAHIDRICO BRIEF:"
        Falls back to a generic UPDATE signature for unknown actions.
    """
    return _SIGNATURES.get(action.lower().strip(), _SIGNATURES["update"])


def all_signatures() -> dict[str, str]:
    """Return all registered signatures."""
    return dict(_SIGNATURES)

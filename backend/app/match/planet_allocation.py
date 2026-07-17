"""Per-planet unit allocation: flat or hierarchical (solar nearness)."""

from __future__ import annotations

from app.domain.models import RootFeature

# Traditional / symbolic nearness to the Sun (identity core).
# Sun & Ascendant peak; Mercury/Venus next; outer bodies fade.
HIERARCHY_BASE: dict[str, float] = {
    "Sun": 1.0,
    "Ascendant": 0.97,
    "Mercury": 0.88,
    "Venus": 0.80,
    "Moon": 0.76,  # personal, but not solar-near
    "Mars": 0.68,
    "Jupiter": 0.48,
    "Saturn": 0.40,
    "Uranus": 0.28,
    "Neptune": 0.24,
    "Pluto": 0.20,
}


def angular_separation_deg(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    diff = abs(float(a) - float(b)) % 360.0
    return min(diff, 360.0 - diff)


def hierarchy_weight(root: RootFeature, sun_abs: float | None) -> float:
    """
    Weight in [~0.12, 1.0].
    Combines fixed solar hierarchy with actual ecliptic nearness to the Sun.
    Sun and Ascendant stay at the top even without abs_pos.
    """
    base = HIERARCHY_BASE.get(root.point_name, 0.22)
    if root.point_name == "Sun":
        return 1.0
    if root.point_name == "Ascendant":
        # Asc is identity mask — peak tier, slight solar-distance softener optional
        sep = angular_separation_deg(root.abs_pos, sun_abs)
        if sep is None:
            return 0.97
        # Still high even if far from sun: 0.90–0.97
        return 0.90 + 0.07 * (1.0 - min(sep, 180.0) / 180.0)

    sep = angular_separation_deg(root.abs_pos, sun_abs)
    if sep is None:
        near = 0.55  # neutral if no positions
    else:
        # Closer to sun on the wheel → higher share
        near = 1.0 - min(sep, 180.0) / 180.0

    # 65% hierarchy + 35% actual solar nearness
    return max(0.12, min(1.0, 0.65 * base + 0.35 * near * base / max(base, 0.2)))


def allocate_units_per_root(
    roots: list[RootFeature],
    units_per_planet: int,
    mode: str = "flat",
) -> dict[str, int]:
    """
    Map root feature id → unit count.

    flat: every root gets units_per_planet.
    hierarchical: Sun/Asc get units_per_planet (peak); others scale by weight.
    """
    peak = max(1, min(100, int(units_per_planet)))
    if not roots:
        return {}

    if mode != "hierarchical":
        return {r.id: peak for r in roots}

    sun = next((r for r in roots if r.point_name == "Sun"), None)
    sun_abs = sun.abs_pos if sun else None

    weights = {r.id: hierarchy_weight(r, sun_abs) for r in roots}
    wmax = max(weights.values()) if weights else 1.0
    if wmax <= 0:
        wmax = 1.0

    out: dict[str, int] = {}
    for r in roots:
        # Scale so the strongest (Sun/Asc) hits peak
        n = int(round(peak * (weights[r.id] / wmax)))
        out[r.id] = max(1, min(100, n))
    # Guarantee Sun & Ascendant are at peak when present
    for r in roots:
        if r.point_name in ("Sun", "Ascendant"):
            out[r.id] = peak
    return out

"""Kerykeion natal + aspect extraction (offline)."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.models import BirthInput, ChartPoint, NatalAspect, NatalChart
from app.domain.tables import link_for_aspect, role_for_point, style_for_sign


ACTIVE_POINTS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Ascendant",
]


def _get_point(subject: Any, name: str) -> Any | None:
    attr = name.lower() if name != "Ascendant" else "first_house"
    # Ascendant is often subject.first_house or subject.ascendant
    candidates = []
    if name == "Ascendant":
        candidates = ["ascendant", "first_house"]
    else:
        candidates = [name.lower(), name]
    for key in candidates:
        val = getattr(subject, key, None)
        if val is not None:
            return val
    return None


def _point_field(point: Any, field: str, default: Any = None) -> Any:
    if point is None:
        return default
    if hasattr(point, field):
        return getattr(point, field)
    if isinstance(point, dict):
        return point.get(field, default)
    return default


def _strength_from_orbit(orbit: float, max_orb: float = 8.0) -> float:
    o = abs(float(orbit))
    if o >= max_orb:
        return 0.05
    return max(0.05, 1.0 - (o / max_orb))


def compute_natal(birth: BirthInput, include_context: bool = False) -> NatalChart:
    from kerykeion import AstrologicalSubjectFactory

    chart_id = birth.id or str(uuid.uuid4())
    subject = AstrologicalSubjectFactory.from_birth_data(
        birth.name,
        birth.year,
        birth.month,
        birth.day,
        birth.hour,
        birth.minute,
        lng=birth.lng,
        lat=birth.lat,
        tz_str=birth.tz_str,
        online=False,
    )

    points: list[ChartPoint] = []
    for name in ACTIVE_POINTS:
        raw = _get_point(subject, name)
        if raw is None:
            continue
        sign = str(_point_field(raw, "sign", "Ari") or "Ari")
        role_meta = role_for_point(name if name != "Ascendant" else "Ascendant")
        style_meta = style_for_sign(sign)
        element = _point_field(raw, "element") or style_meta.get("element")
        quality = _point_field(raw, "quality") or style_meta.get("quality")
        points.append(
            ChartPoint(
                name=name,
                sign=sign,
                element=str(element) if element else None,
                quality=str(quality) if quality else None,
                position=_point_field(raw, "position"),
                abs_pos=_point_field(raw, "abs_pos"),
                house=str(_point_field(raw, "house")) if _point_field(raw, "house") else None,
                retrograde=_point_field(raw, "retrograde"),
                role=role_meta["role"],
                role_label=role_meta["label"],
                style=style_meta["style"],
                style_label=style_meta["label"],
                weight=float(role_meta["weight"]),
            )
        )

    aspects: list[NatalAspect] = []
    try:
        from kerykeion import AspectsFactory

        result = AspectsFactory.single_chart_aspects(subject)
        raw_aspects = getattr(result, "aspects", result) or []
        for a in raw_aspects:
            p1 = str(_point_field(a, "p1_name", "") or "")
            p2 = str(_point_field(a, "p2_name", "") or "")
            # Only aspects between our active set (map Ascendant aliases)
            def _canon(n: str) -> str:
                if n in ("First_House", "Asc", "ASC", "ascendant"):
                    return "Ascendant"
                return n

            p1, p2 = _canon(p1), _canon(p2)
            active_names = {p.name for p in points}
            if p1 not in active_names or p2 not in active_names:
                continue
            aspect_name = str(_point_field(a, "aspect", "") or "")
            orbit = float(_point_field(a, "orbit", 0.0) or 0.0)
            meta = link_for_aspect(aspect_name)
            aspects.append(
                NatalAspect(
                    p1_name=p1,
                    p2_name=p2,
                    aspect=aspect_name,
                    orbit=orbit,
                    aspect_degrees=_point_field(a, "aspect_degrees"),
                    link=meta["link"],
                    polarity=float(meta["polarity"]),
                    strength=_strength_from_orbit(orbit) * float(meta["stance_weight"]),
                )
            )
    except Exception:
        # Aspects optional if factory API differs by version
        aspects = []

    raw_context = None
    if include_context:
        try:
            from kerykeion import to_context

            raw_context = to_context(subject)
        except Exception:
            raw_context = None

    birth_out = birth.model_copy(update={"id": chart_id})
    return NatalChart(
        chart_id=chart_id,
        name=birth.name,
        birth=birth_out,
        points=points,
        aspects=aspects,
        raw_context=raw_context,
    )


def dual_aspects(subject_a: Any, subject_b: Any) -> list[dict]:
    """Return raw dual-chart aspect dicts for relation scoring."""
    try:
        from kerykeion import AspectsFactory

        result = AspectsFactory.dual_chart_aspects(subject_a, subject_b)
        raw = getattr(result, "aspects", result) or []
        out = []
        for a in raw:
            out.append(
                {
                    "p1_name": str(getattr(a, "p1_name", "") or ""),
                    "p2_name": str(getattr(a, "p2_name", "") or ""),
                    "aspect": str(getattr(a, "aspect", "") or ""),
                    "orbit": float(getattr(a, "orbit", 0.0) or 0.0),
                }
            )
        return out
    except Exception:
        return []


def subject_from_birth(birth: BirthInput) -> Any:
    from kerykeion import AstrologicalSubjectFactory

    return AstrologicalSubjectFactory.from_birth_data(
        birth.name,
        birth.year,
        birth.month,
        birth.day,
        birth.hour,
        birth.minute,
        lng=birth.lng,
        lat=birth.lat,
        tz_str=birth.tz_str,
        online=False,
    )

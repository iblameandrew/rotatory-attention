"""Inter-chart partisan relations (conflict / affiliation / neutrality)."""

from __future__ import annotations

from app.charts.kerykeion_service import dual_aspects, subject_from_birth
from app.domain.models import (
    BirthInput,
    NatalChart,
    PartisanRelation,
    RelationDriver,
)
from app.domain.tables import link_for_aspect, role_for_point


def _strength_from_orbit(orbit: float, max_orb: float = 8.0) -> float:
    o = abs(float(orbit))
    if o >= max_orb:
        return 0.05
    return max(0.05, 1.0 - (o / max_orb))


def score_pair_from_aspects(
    aspects: list[dict],
    name_a: str,
    name_b: str,
    chart_a: str,
    chart_b: str,
) -> PartisanRelation:
    total = 0.0
    weight_sum = 0.0
    drivers: list[RelationDriver] = []

    for a in aspects:
        meta = link_for_aspect(a.get("aspect"))
        strength = _strength_from_orbit(float(a.get("orbit", 0.0))) * float(
            meta["stance_weight"]
        )
        pol = float(meta["polarity"])
        total += pol * strength
        weight_sum += strength
        r1 = role_for_point(str(a.get("p1_name", "")))
        r2 = role_for_point(str(a.get("p2_name", "")))
        drivers.append(
            RelationDriver(
                role_a=r1["role"],
                role_b=r2["role"],
                link=meta["link"],
                weight=strength * abs(pol),
                aspect=str(a.get("aspect", "")),
            )
        )

    drivers.sort(key=lambda d: d.weight, reverse=True)
    drivers = drivers[:6]

    if weight_sum < 0.35:
        score = 0.0
        stance = "neutrality"
    else:
        score = max(-1.0, min(1.0, total / max(weight_sum, 1e-6)))
        if score >= 0.22:
            stance = "affiliation"
        elif score <= -0.22:
            stance = "conflict"
        else:
            stance = "neutrality"

    return PartisanRelation(
        chart_a=chart_a,
        chart_b=chart_b,
        name_a=name_a,
        name_b=name_b,
        stance=stance,  # type: ignore[arg-type]
        score=round(score, 4),
        drivers=drivers,
    )


def score_pair_from_styles(chart_a: NatalChart, chart_b: NatalChart) -> PartisanRelation:
    """Fallback when dual aspects unavailable: compare weighted style polarity."""
    # Element harmony heuristic
    elem_affinity = {
        ("fire", "air"): 0.5,
        ("air", "fire"): 0.5,
        ("earth", "water"): 0.5,
        ("water", "earth"): 0.5,
        ("fire", "fire"): 0.2,
        ("earth", "earth"): 0.2,
        ("air", "air"): 0.2,
        ("water", "water"): 0.2,
        ("fire", "water"): -0.55,
        ("water", "fire"): -0.55,
        ("earth", "air"): -0.4,
        ("air", "earth"): -0.4,
        ("fire", "earth"): -0.25,
        ("earth", "fire"): -0.25,
        ("air", "water"): -0.25,
        ("water", "air"): -0.25,
    }

    score = 0.0
    wsum = 0.0
    drivers: list[RelationDriver] = []
    for pa in chart_a.points:
        for pb in chart_b.points:
            ea = (pa.element or "").lower()
            eb = (pb.element or "").lower()
            pol = elem_affinity.get((ea, eb), 0.0)
            # Same style soft bonus (e.g. structure–absorb adjacency via different elements still scored by elem)
            if pa.style == pb.style:
                pol += 0.15
            # Classic "technique needs comprehension" soft adjacency
            adj = {("structure", "absorb"), ("absorb", "structure"), ("refine", "dream"), ("dream", "refine")}
            if (pa.style, pb.style) in adj:
                pol += 0.35
            w = (pa.weight + pb.weight) / 4.0
            score += pol * w
            wsum += w
            if abs(pol) > 0.3:
                drivers.append(
                    RelationDriver(
                        role_a=pa.role,
                        role_b=pb.role,
                        link="harmony" if pol > 0 else "tension",
                        weight=abs(pol) * w,
                    )
                )

    drivers.sort(key=lambda d: d.weight, reverse=True)
    drivers = drivers[:6]
    final = max(-1.0, min(1.0, score / max(wsum, 1e-6)))
    if final >= 0.18:
        stance = "affiliation"
    elif final <= -0.18:
        stance = "conflict"
    else:
        stance = "neutrality"

    return PartisanRelation(
        chart_a=chart_a.chart_id,
        chart_b=chart_b.chart_id,
        name_a=chart_a.name,
        name_b=chart_b.name,
        stance=stance,  # type: ignore[arg-type]
        score=round(final, 4),
        drivers=drivers,
    )


def build_relations(charts: list[NatalChart], births: list[BirthInput]) -> list[PartisanRelation]:
    id_to_birth: dict[str, BirthInput] = {}
    for c, b in zip(charts, births):
        id_to_birth[c.chart_id] = b.model_copy(update={"id": c.chart_id})

    relations: list[PartisanRelation] = []
    for i in range(len(charts)):
        for j in range(i + 1, len(charts)):
            ca, cb = charts[i], charts[j]
            try:
                sa = subject_from_birth(id_to_birth[ca.chart_id])
                sb = subject_from_birth(id_to_birth[cb.chart_id])
                aspects = dual_aspects(sa, sb)
                if aspects:
                    rel = score_pair_from_aspects(
                        aspects, ca.name, cb.name, ca.chart_id, cb.chart_id
                    )
                else:
                    rel = score_pair_from_styles(ca, cb)
            except Exception:
                rel = score_pair_from_styles(ca, cb)
            relations.append(rel)
    return relations

"""Build root + mixture feature graphs from natal charts."""

from __future__ import annotations

from app.domain.models import FeatureGraph, MixtureFeature, NatalChart, RootFeature


def build_feature_graph(chart: NatalChart, max_mixtures: int = 8) -> FeatureGraph:
    roots: list[RootFeature] = []
    point_to_root: dict[str, RootFeature] = {}

    for p in chart.points:
        rid = f"{chart.chart_id}:root:{p.name}"
        root = RootFeature(
            id=rid,
            chart_id=chart.chart_id,
            point_name=p.name,
            role=p.role,
            role_label=p.role_label,
            style=p.style,
            style_label=p.style_label,
            element=p.element,
            quality=p.quality,
            weight=p.weight,
            retrograde=p.retrograde,
        )
        roots.append(root)
        point_to_root[p.name] = root

    # Rank aspects by strength; build mixtures from strongest
    ranked = sorted(chart.aspects, key=lambda a: a.strength, reverse=True)
    mixtures: list[MixtureFeature] = []
    seen_pairs: set[tuple[str, str]] = set()

    for asp in ranked:
        if len(mixtures) >= max_mixtures:
            break
        if asp.p1_name not in point_to_root or asp.p2_name not in point_to_root:
            continue
        pair = tuple(sorted((asp.p1_name, asp.p2_name)))
        if pair in seen_pairs:
            continue
        # Skip very weak
        if asp.strength < 0.2:
            continue
        seen_pairs.add(pair)
        r1 = point_to_root[asp.p1_name]
        r2 = point_to_root[asp.p2_name]
        mid = f"{chart.chart_id}:mix:{asp.p1_name}-{asp.p2_name}:{asp.link}"
        weight = (r1.weight + r2.weight) / 2.0 * asp.strength
        mixtures.append(
            MixtureFeature(
                id=mid,
                chart_id=chart.chart_id,
                parent_ids=[r1.id, r2.id],
                parent_roles=[r1.role, r2.role],
                parent_styles=[r1.style, r2.style],
                link=asp.link,
                strength=asp.strength,
                aspect=asp.aspect,
                weight=weight,
            )
        )

    # Prefer higher weight roots first (stable order)
    roots.sort(key=lambda r: r.weight, reverse=True)
    return FeatureGraph(
        chart_id=chart.chart_id,
        name=chart.name,
        roots=roots,
        mixtures=mixtures,
    )

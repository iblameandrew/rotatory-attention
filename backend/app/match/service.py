"""Full match pipeline."""

from __future__ import annotations

import random
import uuid
from typing import Any

from app.agents.expander import expand_graph
from app.charts.kerykeion_service import compute_natal
from app.config import Settings, get_settings
from app.domain.models import (
    BirthInput,
    FactionManifest,
    FeatureGraph,
    MapSpec,
    MatchManifest,
    MatchOptions,
    NatalChart,
)
from app.domain.tables import faction_color
from app.features.graph_builder import build_feature_graph
from app.match.planet_allocation import allocate_units_per_root
from app.match.relations import build_relations
from app.match.spawner import flatten_agents

# In-memory match store
_MATCHES: dict[str, MatchManifest] = {}


def get_match(match_id: str) -> MatchManifest | None:
    return _MATCHES.get(match_id)


def _map_size_for_factions(n: int) -> list[int]:
    """Grow the field so arbitrarily many factions still have spawn room."""
    # Base 64; +8 per faction after 2, soft-capped for client perf
    side = 64 + max(0, n - 2) * 8
    side = min(side, 160)
    return [side, side]


def _units_per_faction_cap(
    planned_root_units: int,
    mixture_count: int,
    faction_count: int,
    explicit_max: int | None,
    peak_per_planet: int,
) -> int:
    """Roster ceiling from planned planet totals + mixtures."""
    natural = max(1, planned_root_units) + max(0, mixture_count)
    if explicit_max is not None:
        natural = min(natural, explicit_max)
    # Soft global budget so many factions stay playable
    if faction_count > 6:
        budget = max(peak_per_planet * 2, 120 // max(1, faction_count) * peak_per_planet)
        natural = min(natural, max(peak_per_planet, budget))
    return max(peak_per_planet, natural)


def build_match(
    people: list[BirthInput],
    options: MatchOptions | None = None,
    settings: Settings | None = None,
) -> MatchManifest:
    if not people or len(people) < 1:
        raise ValueError("At least one person is required")
    # No upper bound on chart/faction count — N people => N factions.

    options = options or MatchOptions()
    settings = settings or get_settings()
    if options.agent_mode:
        # shallow override without mutating global settings object permanently
        settings = settings.model_copy(update={"agent_mode": options.agent_mode})

    max_mix = options.max_mixtures_per_chart or settings.max_mixtures_per_chart
    units_per_planet = max(1, min(100, int(options.units_per_planet or settings.units_per_planet)))
    spawn_mode = (options.planet_spawn_mode or "flat").strip().lower()
    if spawn_mode not in ("flat", "hierarchical"):
        spawn_mode = "flat"

    charts: list[NatalChart] = []
    graphs: list[FeatureGraph] = []
    for person in people:
        chart = compute_natal(person, include_context=False)
        charts.append(chart)
        graphs.append(build_feature_graph(chart, max_mixtures=max_mix))

    relations = build_relations(charts, people) if len(charts) >= 2 else []

    factions: list[FactionManifest] = []
    for i, (chart, graph) in enumerate(zip(charts, graphs)):
        agents = expand_graph(
            graph,
            settings,
            include_mixtures=options.include_mixtures,
        )
        units_by_root = allocate_units_per_root(
            graph.roots, units_per_planet, mode=spawn_mode
        )
        planned = sum(units_by_root.values())
        mix_count = len(graph.mixtures) if options.include_mixtures else 0
        max_units = _units_per_faction_cap(
            planned_root_units=planned,
            mixture_count=mix_count,
            faction_count=len(people),
            explicit_max=options.max_units_per_faction,
            peak_per_planet=units_per_planet,
        )
        roster = flatten_agents(
            agents,
            graph,
            chart.chart_id,
            max_units=max_units,
            units_per_planet=units_per_planet,
            units_by_root=units_by_root,
        )
        factions.append(
            FactionManifest(
                chart_id=chart.chart_id,
                name=chart.name,
                color=faction_color(i),
                roots=graph.roots,
                mixtures=graph.mixtures if options.include_mixtures else [],
                agents=agents,
                roster=roster,
            )
        )

    seed = options.map_seed if options.map_seed is not None else random.randint(1, 10_000_000)
    match = MatchManifest(
        match_id=str(uuid.uuid4()),
        factions=factions,
        relations=relations,
        map=MapSpec(size=_map_size_for_factions(len(people)), seed=seed),
        meta={
            "agent_mode": settings.agent_mode,
            "people_count": len(people),
            "units_per_planet": units_per_planet,
            "planet_spawn_mode": spawn_mode,
            "unlimited_factions": True,
        },
    )
    _MATCHES[match.match_id] = match
    return match


def natal_summary(person: BirthInput) -> dict[str, Any]:
    chart = compute_natal(person)
    return chart.model_dump()


def features_for_person(person: BirthInput, max_mixtures: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    chart = compute_natal(person)
    graph = build_feature_graph(
        chart, max_mixtures=max_mixtures or settings.max_mixtures_per_chart
    )
    return graph.model_dump()

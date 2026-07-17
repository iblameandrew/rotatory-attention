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
from app.domain.tables import FACTION_COLORS
from app.features.graph_builder import build_feature_graph
from app.match.relations import build_relations
from app.match.spawner import flatten_agents

# In-memory match store
_MATCHES: dict[str, MatchManifest] = {}


def get_match(match_id: str) -> MatchManifest | None:
    return _MATCHES.get(match_id)


def build_match(
    people: list[BirthInput],
    options: MatchOptions | None = None,
    settings: Settings | None = None,
) -> MatchManifest:
    if not people or len(people) < 1:
        raise ValueError("At least one person is required")

    options = options or MatchOptions()
    settings = settings or get_settings()
    if options.agent_mode:
        # shallow override without mutating global settings object permanently
        settings = settings.model_copy(update={"agent_mode": options.agent_mode})

    max_mix = options.max_mixtures_per_chart or settings.max_mixtures_per_chart
    max_units = options.max_units_per_faction or settings.max_units_per_faction

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
        roster = flatten_agents(agents, graph, chart.chart_id, max_units)
        factions.append(
            FactionManifest(
                chart_id=chart.chart_id,
                name=chart.name,
                color=FACTION_COLORS[i % len(FACTION_COLORS)],
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
        map=MapSpec(size=[64, 64], seed=seed),
        meta={
            "agent_mode": settings.agent_mode,
            "people_count": len(people),
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

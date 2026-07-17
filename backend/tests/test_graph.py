from app.domain.models import BirthInput, ChartPoint, NatalAspect, NatalChart
from app.features.graph_builder import build_feature_graph


def _point(name: str, sign: str, role: str, style: str, weight: float = 1.0) -> ChartPoint:
    return ChartPoint(
        name=name,
        sign=sign,
        role=role,
        role_label=role.title(),
        style=style,
        style_label=style.title(),
        weight=weight,
        element="earth",
        quality="cardinal",
    )


def test_build_roots_and_mixtures():
    chart = NatalChart(
        chart_id="c1",
        name="Test",
        birth=BirthInput(
            name="Test",
            year=1990,
            month=1,
            day=1,
            hour=12,
            minute=0,
            lat=0,
            lng=0,
            tz_str="UTC",
        ),
        points=[
            _point("Sun", "Cap", "drive", "structure", 2.0),
            _point("Neptune", "Pis", "dream", "absorb", 0.85),
            _point("Mars", "Ari", "force", "ignite", 1.5),
        ],
        aspects=[
            NatalAspect(
                p1_name="Sun",
                p2_name="Neptune",
                aspect="sextile",
                orbit=1.2,
                link="harmony",
                polarity=0.7,
                strength=0.9,
            ),
            NatalAspect(
                p1_name="Sun",
                p2_name="Mars",
                aspect="square",
                orbit=2.0,
                link="tension",
                polarity=-0.8,
                strength=0.7,
            ),
        ],
    )
    g = build_feature_graph(chart, max_mixtures=4)
    assert len(g.roots) == 3
    assert g.roots[0].role == "drive"
    assert len(g.mixtures) >= 1
    assert any(m.link == "harmony" for m in g.mixtures)
